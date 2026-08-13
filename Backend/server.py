import sys
import json
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from automation.validator import DashboardValidator

# Initialize FastAPI
app = FastAPI(title="PowerBI QA Agent API")

# Add CORS just in case your frontend needs it for standard API calls later
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

@app.websocket("/ws/validate")
async def websocket_validate(websocket: WebSocket):
    """Real-time WebSocket endpoint for the React Frontend."""
    await websocket.accept()
    
    # Wait for the frontend to send the URLs
    data = await websocket.receive_text()
    request = json.loads(data)
    
    async def send_log(message: dict):
        await websocket.send_json(message)

    try:
        validator = DashboardValidator(send_log=send_log)
        # Using the sequential execution logic we set up earlier
        await validator.run_comparison_suite(
            source_url=request.get("source_url"),
            target_url=request.get("target_url")
        )
    except WebSocketDisconnect:
        print("Client disconnected from WebSocket.")
    except Exception as e:
        await websocket.send_json({"event": "ERROR", "message": str(e)})

async def run_server():
    """Configures and runs the Uvicorn server programmatically."""
    config = uvicorn.Config(
        "server:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    # --- YOUR FRIEND'S BRILLIANT PYTHON 3.14 FIX ---
    try:
        if sys.platform == "win32":
            # Forces the correct Event Loop for Playwright on Windows without deprecation warnings
            asyncio.run(run_server(), loop_factory=asyncio.ProactorEventLoop)
        else:
            asyncio.run(run_server())
    except Exception as e:
        print(f"Failed to start server: {e}")