"""
SonarFT Entry Point
"""
import asyncio
import logging
import logging.handlers
import os
from uvicorn import Config, Server
from sonarft_server import SonarftServer


def setup_file_logging() -> None:
    """
    Configure a rotating file handler for persistent server-side logs.
    Reads LOG_DIR (default: sonarftdata/logs) and LOG_LEVEL (default: INFO).
    Rotates at 10 MB, keeps 5 backups.
    """
    log_dir = os.environ.get("LOG_DIR", os.path.join("sonarftdata", "logs"))
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "sonarft.log")
    log_level = getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(log_level)
    root.addHandler(handler)

    # Also keep console output
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)


async def start_app():
    """
    Asynchronously start the sonarft server application.
    """
    import os
    server = SonarftServer()
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    config = Config(app=server.app, host=host, port=port)
    server_instance = Server(config)
    await server_instance.serve()


if __name__ == "__main__":
    setup_file_logging()
    asyncio.run(start_app())