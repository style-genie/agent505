import base64
import io
import logging
import os
import dotenv
import json
import sys


from typing import Dict, List, Optional
import asyncio
from dataclasses import dataclass
from pydantic import BaseModel
import uvicorn
from uuid import uuid4
from uuid import UUID


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



async def stream_task_progress(manager: ConnectionManager, task_id: str):
    while True:
        task = manager.tasks.get(task_id)
        if task:
            yield json.dumps({
                "task_id": task.id,
                "status": task.status,
                "progress": task.progress
            })
        await asyncio.sleep(1)

