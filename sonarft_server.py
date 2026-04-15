"""
SonarFT Communication Module
Interface between the Web App and Trading Bot
"""
import os
import re
import json
import logging
import asyncio
from collections import deque
from typing import Dict, List, Optional
from starlette.websockets import WebSocketDisconnect
from fastapi import Request, Depends
from fastapi import HTTPException, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from sonarft_manager import BotManager

_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')

# Load API token from environment — set SONARFT_API_TOKEN before starting the server.
# If not set, authentication is disabled (development mode only).
_API_TOKEN: Optional[str] = os.environ.get("SONARFT_API_TOKEN")
if not _API_TOKEN:
    logging.getLogger(__name__).warning(
        "SONARFT_API_TOKEN is not set — all HTTP and WebSocket endpoints are publicly accessible. "
        "Set this environment variable before deploying to production."
    )
_bearer_scheme = HTTPBearer(auto_error=False)

def _require_auth(credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme)) -> None:
    """Dependency: reject requests that do not carry the correct Bearer token."""
    if not _API_TOKEN:
        return  # auth disabled — no token configured
    if credentials is None or credentials.credentials != _API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

def _validate_id(value: str, label: str = "identifier") -> str:
    """Raise HTTP 400 if value contains path traversal or invalid characters."""
    if not _ID_PATTERN.match(value):
        raise HTTPException(status_code=400, detail=f"Invalid {label}")
    return value


# ### SonarftServer Class - ##########################################
class SonarftServer:
    """
    Server for SonarFT application, providing WebSocket communication and logging.
    """

    def __init__(self):
        """
        Initializes the SonarftServer with a BotManager, actions dictionary, FastAPI application,
        WebSocket connections dictionary, and tasks list.
        """
        self.botmanager = BotManager()
        self.actions = {
            "create": "create_bot",
            "remove": "remove_bot",
            "run": "run_bot",
        }
        self._max_bots_per_client = int(os.environ.get("MAX_BOTS_PER_CLIENT", "5"))

        self.app: FastAPI = FastAPI()

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["https://sonarft.com", "http://localhost:3000"],
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type"],
        )

        self.connections: Dict[str, WebSocket] = {}
        self.tasks: List[asyncio.Task] = []

        self.setup_http_endpoints()
        self.setup_ws_endpoints()

    # SonarftServer HTTP Methods
    def setup_http_endpoints(self):
        """
        Setup http endpoints for the Web App calls
        """

        @self.app.get("/botids/{client_id}")
        def get_botids(client_id: str, _: None = Depends(_require_auth)):
            return {"botids": self.botmanager.get_botids(client_id)}

        @self.app.get("/default_parameters")
        async def get_default_parameters(_: None = Depends(_require_auth)):
            try:
                with open(
                    "sonarftdata/config/parameters.json", "r", encoding="utf-8"
                ) as read_file:
                    data = json.load(read_file)
                return data
            except FileNotFoundError as exc:
                raise HTTPException(status_code=404, detail="File not found") from exc
            except Exception as error:
                logging.getLogger(__name__).error(f"get_default_parameters error: {error}")
                raise HTTPException(status_code=500, detail="Internal server error") from error

        @self.app.get("/default_indicators")
        async def get_default_indicators(_: None = Depends(_require_auth)):
            try:
                with open(
                    "sonarftdata/config/indicators.json", "r", encoding="utf-8"
                ) as read_file:
                    data = json.load(read_file)
                return data
            except FileNotFoundError as exc:
                raise HTTPException(status_code=404, detail="File not found") from exc
            except Exception as error:
                logging.getLogger(__name__).error(f"get_default_indicators error: {error}")
                raise HTTPException(status_code=500, detail="Internal server error") from error

        @self.app.get("/bot/get_parameters/{client_id}")
        async def get_bot_parameters(client_id: str, _: None = Depends(_require_auth)):
            _validate_id(client_id, "client_id")
            try:
                with open(
                    f"sonarftdata/config/{client_id}_parameters.json", "r", encoding="utf-8"
                ) as read_file:
                    data = json.load(read_file)
                return data
            except FileNotFoundError as exc:
                raise HTTPException(status_code=404, detail="File not found") from exc
            except Exception as error:
                logging.getLogger(__name__).error(f"get_bot_parameters error: {error}")
                raise HTTPException(status_code=500, detail="Internal server error") from error

        @self.app.post("/bot/set_parameters/{client_id}")
        async def set_bot_parameters(client_id: str, new_parameters: dict = Body(...), _: None = Depends(_require_auth)):
            _validate_id(client_id, "client_id")
            try:
                with open(f"sonarftdata/config/{client_id}_parameters.json", "w", encoding="utf-8") as write_file:
                    json.dump(new_parameters, write_file, ensure_ascii=False, indent=4)
                return {"message": f"Parameters for client: {client_id} set successfully."}
            except FileNotFoundError as exc:
                raise HTTPException(status_code=404, detail="File not found") from exc
            except Exception as error:
                logging.getLogger(__name__).error(f"set_bot_parameters error: {error}")
                raise HTTPException(status_code=500, detail="Internal server error") from error
    
        @self.app.get("/bot/get_indicators/{client_id}")
        async def get_bot_indicators(client_id: str, _: None = Depends(_require_auth)):
            _validate_id(client_id, "client_id")
            try:
                with open(
                    f"sonarftdata/config/{client_id}_indicators.json", "r", encoding="utf-8"
                ) as read_file:
                    data = json.load(read_file)
                return data
            except FileNotFoundError as exc:
                raise HTTPException(status_code=404, detail="File not found") from exc
            except Exception as error:
                logging.getLogger(__name__).error(f"get_bot_indicators error: {error}")
                raise HTTPException(status_code=500, detail="Internal server error") from error

        @self.app.post("/bot/set_indicators/{client_id}")
        async def set_bot_indicators(client_id: str, new_indicators: dict = Body(...), _: None = Depends(_require_auth)):
            _validate_id(client_id, "client_id")
            try:
                with open(f"sonarftdata/config/{client_id}_indicators.json", "w", encoding="utf-8") as write_file:
                    json.dump(new_indicators, write_file, ensure_ascii=False, indent=4)
                return {"message": f"Indicators for client: {client_id} set successfully."}
            except FileNotFoundError as exc:
                raise HTTPException(status_code=404, detail="File not found") from exc
            except Exception as error:
                logging.getLogger(__name__).error(f"set_bot_indicators error: {error}")
                raise HTTPException(status_code=500, detail="Internal server error") from error

        @self.app.get("/bot/{botid}/orders")
        async def get_bot_orders(botid: str, _: None = Depends(_require_auth)):
            _validate_id(botid, "botid")
            try:
                with open(
                    f"sonarftdata/history/{botid}_orders.json", "r", encoding="utf-8"
                ) as read_file:
                    data = json.load(read_file)
                return data
            except FileNotFoundError as exc:
                raise HTTPException(status_code=404, detail="File not found") from exc
            except Exception as error:
                logging.getLogger(__name__).error(f"get_bot_orders error: {error}")
                raise HTTPException(status_code=500, detail="Internal server error") from error

        @self.app.get("/bot/{botid}/trades")
        async def get_bot_trades(botid: str, _: None = Depends(_require_auth)):
            _validate_id(botid, "botid")
            try:
                with open(
                    f"sonarftdata/history/{botid}_trades.json", "r", encoding="utf-8"
                ) as read_file:
                    data = json.load(read_file)
                return data
            except FileNotFoundError as exc:
                raise HTTPException(status_code=404, detail="File not found") from exc
            except Exception as error:
                logging.getLogger(__name__).error(f"get_bot_trades error: {error}")
                raise HTTPException(status_code=500, detail="Internal server error") from error

    # SonarftServer WEBSOCKET Methods
    def setup_ws_endpoints(self):
        """
        Setup ws endpoints for the Web App calls
        """

        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str, token: Optional[str] = None):
            if _API_TOKEN and token != _API_TOKEN:
                await websocket.close(code=1008)  # Policy Violation
                return

            _validate_id(client_id, "client_id")
            logger = self.setup_logging(client_id)
            self.botmanager.logger = logger

            await websocket.accept()
            # if self.connections[client_id].client_state == WebSocketDisconnect:
            self.connections[client_id] = websocket
            log_processor = asyncio.create_task(
                logger.handlers[0].consume_logs(client_id)
            )
            await asyncio.sleep(1)
            logger.info(
                "Client: %s has been connected to %s!",
                client_id,
                self.connections[client_id].client_state,
            )

            while True:
                try:
                    await self.process_websocket_tasks(websocket, client_id, log_processor)
                except WebSocketDisconnect:
                    self.handle_disconnection(client_id, log_processor)
                    return

    async def process_websocket_tasks(self, websocket, client_id, log_processor):
        """
        Process ws tasks

        Parameters:
        websocket
        client_id (str): The ID of the client the log is associated with.
        log_processor
        """
        receive_task = asyncio.create_task(websocket.receive_text())
        send_task = asyncio.create_task(self.send_logs(websocket, client_id))

        done, pending = await asyncio.wait(
            [receive_task, send_task], return_when=asyncio.FIRST_COMPLETED
        )

        if receive_task in done:
            await self.process_received_task(receive_task, client_id, log_processor)
        else:
            receive_task.cancel()

        for send_task in pending:
            send_task.cancel()

        self.cleanup_done_tasks()

    async def process_received_task(self, receive_task, client_id, log_processor):
        """
        Process ws received tasks

        Parameters:
        receive_task
        client_id (str): The ID of the client the log is associated with.
        log_processor
        """
        try:
            data = receive_task.result()
            event = self.decode_json(data)

            if not event or "type" not in event or "key" not in event:
                return

            botid = event.get("botid")
            action = self.actions.get(event["key"])
            self.botmanager.logger.info(f"client: {client_id} - Botid: {botid} - Action: {action}")

            if action:
                await self.perform_action(action, botid, client_id)
        except WebSocketDisconnect:
            self.handle_disconnection(client_id, log_processor)
            raise  # re-raise so the outer loop catches it and exits

    async def perform_action(self, action, botid, client_id):
        """
        Perform required action, enforcing max bots per client limit on create.
        """
        if action == 'create_bot':
            current_bots = len(self.botmanager.get_botids(client_id))
            if current_bots >= self._max_bots_per_client:
                self.botmanager.logger.warning(
                    f"Client {client_id} has reached the max bot limit "
                    f"({self._max_bots_per_client}). Ignoring create request."
                )
                return
        action_method = getattr(self.botmanager, action)
        task = asyncio.create_task(action_method(botid or client_id))

        if not botid:
            botid = task

        self.botmanager.logger.info(f"Task {task} has been created")

        with TaskManager(self.tasks):
            self.tasks.append(task)

    def handle_disconnection(self, client_id, log_processor):
        """
        Handle client disconnection

        Parameters:
        client_id
        log_processor
        """
        self.botmanager.logger.info(f"Client: {client_id} has been disconnected")
        if client_id in self.connections:
            del self.connections[client_id]
        log_processor.cancel()

    def cleanup_done_tasks(self):
        for task in list(self.tasks):
            if task.done():
                exc = task.exception()
                if exc:
                    self.botmanager.logger.error(f"Task raised exception: {exc}")
                self.botmanager.logger.info(f"Task {task} has been removed")
                self.tasks.remove(task)

    # SonarftServer JSON
    def decode_json(self, data):
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            self.botmanager.logger.warning(f"Failed to decode JSON: {data}")

    # SonarftServer LOGS
    def setup_logging(self, client_id):
        """
        Setup logging for a specific client.

        Parameters:
        client_id (str): The ID of the client for which logging should be setup.

        Returns:
        logger: The configured logger for the client.
        """
        log_format: str = "%(levelname)s - %(client_id)s - %(message)s"
        handler: AsyncHandler = AsyncHandler()
        handler.addFilter(ClientIdFilter(client_id))
        handler.setFormatter(logging.Formatter(log_format))
        logger: logging.Logger = logging.getLogger(client_id)
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        return logger

    async def send_logs(self, websocket: WebSocket, client_id: str):
        """
        Send logs to a client through WebSocket.

        Parameters:
        websocket (WebSocket): The WebSocket connection.
        client_id (str): The ID of the client to send logs to.
        """
        handler = logging.getLogger(client_id).handlers[0]
        while True:
            if client_id in handler.logs and handler.logs[client_id]:
                message: str = handler.logs[client_id].popleft()
                await websocket.send_text(f"{message}")
            else:
                await asyncio.sleep(1)

    # SonarftServer ERRORS
    def setup_error_handlings(self):
        """
        Handling errors
        """

        @self.app.exception_handler(Exception)
        async def custom_exception_handler(_request: Request, exc: Exception):
            return JSONResponse(
                status_code=500,
                content={"message": f"An error occurred: {exc}"},
            )


# ### SonarftServer Support Classes - ################################
# ### AsyncHandler Class ###
class AsyncHandler(logging.Handler):
    """
    Asynchronous handler for logging. This class inherits from logging.Handler.
    """

    def __init__(self):
        """
        Initializes the AsyncHandler with a logs queue and a dictionary for per-client logs.
        """
        super().__init__()
        self.logs_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.logs: Dict[str, deque] = {}

    def emit(self, record: logging.LogRecord) -> None:
        """
        Put the log record into the logs queue.

        Parameters:
        record (logging.LogRecord): The log record to be put into the queue.
        """
        try:
            self.logs_queue.put_nowait(record)
        except asyncio.QueueFull:
            pass  # drop oldest-equivalent: queue is full, discard this record

    async def async_emit(self, record: logging.LogRecord, client_id: str) -> None:
        """
        Asynchronously format and store the log record.

        Parameters:
        record (logging.LogRecord): The log record to be stored.
        client_id (str): The ID of the client the log is associated with.
        """
        log_message: str = self.format(record)
        if client_id not in self.logs:
            self.logs[client_id] = deque(maxlen=1000)
        self.logs[client_id].append(log_message)

    async def consume_logs(self, client_id: str) -> None:
        """
        Asynchronously consume logs from the logs queue for a specific client.

        Parameters:
        client_id (str): The ID of the client whose logs are to be consumed.
        """
        while True:
            try:
                record: logging.LogRecord = await self.logs_queue.get()
                await self.async_emit(record, client_id)
            except Exception as e:
                logging.getLogger(__name__).error(f"consume_logs error for {client_id}: {e}")


# ### ClientIdFilter Class ###
class ClientIdFilter(logging.Filter):
    """
    Filter for logging based on client ID. This class inherits from logging.Filter.
    """

    def __init__(self, client_id):
        """
        Initializes the ClientIdFilter with a client ID.

        Parameters:
        client_id: The ID of the client.
        """
        super().__init__()
        self.client_id = client_id

    def filter(self, record):
        """
        Filter method to add client ID to the log record.

        Parameters:
        record: The log record to be filtered.
        """
        record.client_id = self.client_id
        return True


# ### TaskManager Class ###
class TaskManager:
    """
    Manage created tasks
    Args:
        tasks
    """

    def __init__(self, tasks):
        self.tasks = tasks

    def __enter__(self):
        return self

    def __exit__(self, _type, _value, _traceback):
        for task in list(self.tasks):
            if task.done():
                self.tasks.remove(task)
