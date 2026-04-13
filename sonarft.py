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
    server = SonarftServer()
    config = Config(app=server.app, host="127.0.0.1", port=5000)
    server_instance = Server(config)
    await server_instance.serve()


if __name__ == "__main__":
    asyncio.run(start_app())