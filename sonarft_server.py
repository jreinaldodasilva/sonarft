"""
SonarFT Communication Module
Interface between the Web App and Trading Bot
"""
import os
import re
import json
import logging
import asyncio
import urllib.request
from collections import deque
from typing import Dict, List, Optional
from starlette.websockets import WebSocketDisconnect
from fastapi import Request, Depends
from fastapi import HTTPException, Body
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient, InvalidTokenError

from sonarft_manager import BotManager

_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,64}$')
_logger = logging.getLogger(__name__)


def _read_json(path: str) -> dict:
    """Synchronous JSON read — intended to run inside asyncio.to_thread."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _write_json(path: str, data: dict) -> None:
    """Synchronous JSON write — intended to run inside asyncio.to_thread."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ### Authentication ###################################################
#
# Auth mode is determined by environment variables:
#
#   NETLIFY_SITE_URL  — set to your Netlify site URL (e.g. https://sonarft.netlify.app)
#                       Enables Netlify JWT validation via JWKS.
#
#   SONARFT_API_TOKEN — static Bearer token fallback (non-Netlify deployments).
#
# If neither is set, auth is disabled (development mode only).

_NETLIFY_SITE_URL: Optional[str] = os.environ.get("NETLIFY_SITE_URL", "").rstrip("/")
_API_TOKEN: Optional[str] = os.environ.get("SONARFT_API_TOKEN")

# PyJWKClient caches JWKS keys and refreshes them automatically.
_jwks_client: Optional[PyJWKClient] = None
if _NETLIFY_SITE_URL:
    _jwks_client = PyJWKClient(f"{_NETLIFY_SITE_URL}/.netlify/identity/keys")
    _logger.info("Netlify JWT auth enabled — JWKS: %s/.netlify/identity/keys", _NETLIFY_SITE_URL)
elif _API_TOKEN:
    _logger.info("Static token auth enabled via SONARFT_API_TOKEN.")
else:
    _logger.warning(
        "No auth configured (NETLIFY_SITE_URL and SONARFT_API_TOKEN are both unset). "
        "All endpoints are publicly accessible. Set one before deploying to production."
    )

_bearer_scheme = HTTPBearer(auto_error=False)


def _verify_token(token: Optional[str]) -> None:
    """
    Validate a Bearer token against the configured auth mode.
    Raises HTTPException(401) on failure.
    """
    # Auth disabled — allow all
    if not _NETLIFY_SITE_URL and not _API_TOKEN:
        return

    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Netlify JWT validation
    if _jwks_client:
        try:
            signing_key = _jwks_client.get_signing_key_from_jwt(token)
            jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience="netlify",
                options={"verify_exp": True},
            )
            return
        except InvalidTokenError as e:
            _logger.warning("JWT validation failed: %s", e)
            raise HTTPException(status_code=401, detail="Unauthorized") from e

    # Static token fallback
    if _API_TOKEN and token != _API_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _require_auth(credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme)) -> None:
    """FastAPI dependency: validates the Bearer token from the Authorization header."""
    token = credentials.credentials if credentials else None
    _verify_token(token)


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
            "set_simulation": "set_simulation_mode",
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

        @self.app.post("/emergency_stop")
        async def emergency_stop(_: None = Depends(_require_auth)):
            """Stop all running bots immediately."""
            stopped = []
            for client_id, botids in list(self.botmanager._clients.items()):
                for botid in list(botids):
                    await self.botmanager.remove_bot(botid)
                    stopped.append(botid)
            logging.getLogger(__name__).warning(
                f"EMERGENCY STOP triggered — stopped {len(stopped)} bot(s): {stopped}"
            )
            return {"stopped": stopped, "count": len(stopped)}

        @self.app.get("/default_parameters")
        async def get_default_parameters(_: None = Depends(_require_auth)):
            try:
                data = await asyncio.to_thread(
                    _read_json, "sonarftdata/config/parameters.json"
                )
                return data
            except FileNotFoundError as exc:
                raise HTTPException(status_code=404, detail="File not found") from exc
            except Exception as error:
                logging.getLogger(__name__).error(f"get_default_parameters error: {error}")
                raise HTTPException(status_code=500, detail="Internal server error") from error

        @self.app.get("/default_indicators")
        async def get_default_indicators(_: None = Depends(_require_auth)):
            try:
                data = await asyncio.to_thread(
                    _read_json, "sonarftdata/config/indicators.json"
                )
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
                data = await asyncio.to_thread(
                    _read_json, f"sonarftdata/config/{client_id}_parameters.json"
                )
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
                await asyncio.to_thread(
                    _write_json, f"sonarftdata/config/{client_id}_parameters.json", new_parameters
                )
                # Hot-reload: apply to all running bots owned by this client
                await self.botmanager.reload_parameters(client_id, new_parameters)
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
                data = await asyncio.to_thread(
                    _read_json, f"sonarftdata/config/{client_id}_indicators.json"
                )
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
                await asyncio.to_thread(
                    _write_json, f"sonarftdata/config/{client_id}_indicators.json", new_indicators
                )
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
                from sonarft_helpers import SonarftHelpers
                data = await SonarftHelpers._async_query('orders', botid)
                return data
            except Exception as error:
                logging.getLogger(__name__).error(f"get_bot_orders error: {error}")
                raise HTTPException(status_code=500, detail="Internal server error") from error

        @self.app.get("/bot/{botid}/trades")
        async def get_bot_trades(botid: str, _: None = Depends(_require_auth)):
            _validate_id(botid, "botid")
            try:
                from sonarft_helpers import SonarftHelpers
                data = await SonarftHelpers._async_query('trades', botid)
                return data
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
            try:
                _verify_token(token)
            except HTTPException:
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
                # set_simulation passes a value parameter
                if action == "set_simulation_mode":
                    value = event.get("value", True)
                    await self.perform_action(action, botid or client_id, client_id, value=value)
                else:
                    await self.perform_action(action, botid, client_id)
        except WebSocketDisconnect:
            self.handle_disconnection(client_id, log_processor)
            raise  # re-raise so the outer loop catches it and exits

    async def perform_action(self, action, botid, client_id, **kwargs):
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
        action_method = getattr(self.botmanager, action, None)
        if not action_method:
            self.botmanager.logger.warning(f"Unknown action: {action}")
            return
        task = asyncio.create_task(action_method(botid or client_id, **kwargs))

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
        Send structured JSON events to the client over WebSocket.

        Each message is a JSON object with a 'type' field:
          {"type": "log", "level": "INFO", "message": "...", "ts": 1234567890}

        Lifecycle events are emitted alongside the log when detected:
          {"type": "bot_created", "botid": "...", "ts": 1234567890}
          {"type": "bot_removed", "botid": "...", "ts": 1234567890}
          {"type": "order_success", "ts": 1234567890}
          {"type": "trade_success", "ts": 1234567890}

        Parameters:
        websocket (WebSocket): The WebSocket connection.
        client_id (str): The ID of the client to send logs to.
        """
        import time
        handler = logging.getLogger(client_id).handlers[0]

        # Sentinel strings — kept in sync with sonarft_manager / sonarft_bot log output.
        _BOT_CREATED  = "Bot CREATED!"
        _BOT_REMOVED  = "Bot REMOVED!"
        _ORDER_SUCCESS = "Order: Success"
        _TRADE_SUCCESS = "Trade: Success"

        while True:
            if client_id in handler.logs and handler.logs[client_id]:
                message: str = handler.logs[client_id].popleft()
                ts = int(time.time())

                # Determine log level from message prefix (e.g. "INFO - client - ...").
                level = "INFO"
                if message.startswith("WARNING"):
                    level = "WARNING"
                elif message.startswith("ERROR"):
                    level = "ERROR"

                # Always send the log line.
                await websocket.send_text(json.dumps({
                    "type": "log",
                    "level": level,
                    "message": message,
                    "ts": ts,
                }))

                # Emit structured lifecycle events alongside the log.
                if _BOT_CREATED in message:
                    # Extract botid from message if present (format: "Bot <botid> CREATED!").
                    botid = None
                    parts = message.split()
                    if len(parts) >= 2:
                        botid = parts[1] if parts[1] != "CREATED!" else None
                    await websocket.send_text(json.dumps({
                        "type": "bot_created",
                        "botid": botid,
                        "ts": ts,
                    }))

                elif _BOT_REMOVED in message:
                    botid = None
                    parts = message.split()
                    if len(parts) >= 2:
                        botid = parts[1] if parts[1] != "REMOVED!" else None
                    await websocket.send_text(json.dumps({
                        "type": "bot_removed",
                        "botid": botid,
                        "ts": ts,
                    }))

                if _ORDER_SUCCESS in message:
                    await websocket.send_text(json.dumps({
                        "type": "order_success",
                        "ts": ts,
                    }))

                if _TRADE_SUCCESS in message:
                    await websocket.send_text(json.dumps({
                        "type": "trade_success",
                        "ts": ts,
                    }))
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
