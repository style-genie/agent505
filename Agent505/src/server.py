import base64
import io
import logging
import os
import dotenv
import json
import sys
# from src.ai.img_to_img import ImgToImg
from Agent505.src.session import Session
from fastapi.middleware import cors
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, middleware, Response, HTTPException
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    ORJSONResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
    UJSONResponse,
)
from typing import Dict, List, Optional
import asyncio
from dataclasses import dataclass
from pydantic import BaseModel
import uvicorn
from uuid import uuid4
from uuid import UUID


#   --------> LOGGER <--------
logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.DEBUG,
)

logger = logging.getLogger(__name__)
#   --------> SESSIONS <--------
Sessions=[]

# --------> Load environment variables <--------
dotenv.load_dotenv("./.env.local")

# -------> Create FastAPI app <------
app = FastAPI(
    title="StyleGenie API",
    description="AI-Powered Style Assistant API",
    version="0.1.0",
)
# Get allowed origins from environment variable or use default
allowed_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
# Add CORS middleware
app.add_middleware(
    cors.CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------> USER_SESSION <----------
class SessionData(BaseModel):
    username: str

cookie_params = CookieParameters()

# Uses UUID
cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key="DONOTUSE",
    cookie_params=cookie_params,
)

backend = InMemoryBackend[UUID, SessionData]()
@dataclass
class Task:
    id: str
    status: str
    progress: float
    children: List['Task']
    
# ----------> WEBSOCKET MANAGER <----------
class ConnectionManager:
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.tasks: Dict[str, Task] = {}
        self.respondMsgs={}
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_personal_message(self, session_id: str, message: dict):
        print("Sending personal message to", session_id)
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)
        else:
            raise WebSocketDisconnect(code=404, reason="Session not found")

    async def broadcast_task_update(self, task_id: str, status: str, progress: float):
        update = {"task_id": task_id, "status": status, "progress": progress}
        for ws in self.active_connections.values():
            await ws.send_json(update)

    async def receive_text(self, uuid, websocket: WebSocket):
        """Receives text from the WebSocket in a parallel async task and returns a promise."""
        try:
            
                self.respondMsgs[uuid   ]=None
                response= await websocket.receive_text()
                resp_name=response.uuid
                print("respond name: " + resp_name+ " response: " + response)

        except WebSocketDisconnect:
            return None
manager = ConnectionManager()

async def stream_task_progress(task_id: str):
    while True:
        task = manager.tasks.get(task_id)
        if task:
            yield json.dumps({
                "task_id": task.id,
                "status": task.status,
                "progress": task.progress
            })
        await asyncio.sleep(1)
        
# ------> CREATE_AGENT_SESSION <----------
@app.post("/create_session/{name}")
async def create_session(name: str, response: Response):
    session = uuid4()
    data = SessionData(username=name)
    await backend.create(session, data)
    cookie.attach_to_response(response, session)
    return f"created session for {name}"

# ------> Existing_SESSION <----------
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        session = Session(manager,websocket, session_id=session_id)
        Sessions.append(session)
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"Error creating agent session: {e}")
        manager.disconnect(session_id)


def start():
    uvicorn.run(
        # WICHTIG: fuer reload=True ist es besser, den Import-String anzugeben.
        # Uvicorn muss wissen, wie es deine App neu laden kann.
        "main:app",
        host="127.0.0.1",
        port=1500,
        reload=True  # Aktiviert Auto-Reload bei Code-Änderungen (gut für Entwicklung)
        # log_level="info" # Optional: Setze das Logging-Level
    )


