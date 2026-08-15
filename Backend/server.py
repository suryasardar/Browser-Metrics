import sys
import json
import logging
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from automation.validator import DashboardValidator

# Initialize System Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("server")

app = FastAPI(title="PowerBI QA Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ValidateRequest(BaseModel):
    source_url: str
    target_url: str

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.websocket("/ws/validate")
async def websocket_validate(websocket: WebSocket):
    """Real-time WebSocket endpoint for React UI logs and results."""
    await websocket.accept()
    logger.info("WebSocket connection established with client.")
    
    try:
        data = await websocket.receive_text()
        request = json.loads(data)
        logger.info(f"Received validation request for Source: {request.get('source_url')[:30]}...")
        
        async def send_log(message: dict):
            await websocket.send_json(message)

        validator = DashboardValidator(send_log=send_log)
        await validator.run_comparison_suite(
            source_url=request.get("source_url"),
            target_url=request.get("target_url")
        )
    except WebSocketDisconnect:
        logger.info("Client disconnected from WebSocket.")
    except Exception as e:
        logger.error(f"Unhandled WebSocket error: {e}")
        await websocket.send_json({"event": "ERROR", "message": str(e)})

async def run_server():
    """Configures and launches Uvicorn server instance."""
    config = uvicorn.Config(
        "server:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    logger.info("Initializing Backend Server...")
    try:
        if sys.platform == "win32":
            # Force ProactorEventLoop for Python 3.14 Windows compatibility
            asyncio.run(run_server(), loop_factory=asyncio.ProactorEventLoop)
        else:
            asyncio.run(run_server())
    except Exception as e:
        logger.critical(f"Failed to start server: {e}")