"""
SonarFT Entry Point
"""
import asyncio
from uvicorn import Config, Server
from sonarft_server import SonarftServer

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
    asyncio.run(start_app())