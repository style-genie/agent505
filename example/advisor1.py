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


instruction_message ={"role": "system", "content": "you are a friendly assistant"}
instruction_message2 ={"role": "system", "content": """
                    You are a fashion instructor. 
                    You must help the user to find the perfect outfits that match their preferences. 
                    Here are some important instructions you must follow:
                    - document your steps and output in on readable json format.
                    - your output must be a json object.
                    - your output must have the same format as the example:
                        output = {
                        "achievements": ['''
                            - step 1: ask the user for their preferences
                        ''',],
                        "next_steps:'''
                            - step 2: use the get_json_element_by_id function to get the data from data.json
                            - step 3: use the fetch_elements_from_vector_db function to get the data from the vector database
                        ''',
                        "user_feedback_required": False,
                        "markdown_media_portal":'''
                            I found some addionation for you that i wanna share with you:
                            ## Clothing recommendation
                            - i was looking for some darker colors that mach your bright hair
                            - for the trouser i selected a blue color as you wanted
                            ### Trend insights
                            - the nike sportswear collection is very popular right now, i collected some data from the internet for you:
                            - image: !(image)[https://images.unsplash.com/photo]
                            - forbes reported that nike sportswear is the most popular brand in the world:
                                - https://www.forbes.com/sites/forbestechcouncil/2022/08/02/nike-sportswear-earnings-2022/#6b2e1b5d7f4f
                                > the also reported that nike sportswear was sold more than any other brand in the world, here is the data:
                                - https://www.forbes.com/sites/forbestechcouncil/2022/08/02/nike-sportswear-earnings-2022/#6b2e1b5d7f4f
                        '''
                        "tools_required_next": ["get_json_element_by_id", "fetch_elements_from_vector_db"],
                        "important_notes": "You must use the tools in order to get the data. The user noted that it is important to find armani only!",
                        "task_finished": False,
                        "step_failed": False
                        }
                    """
}

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
    try:
        # connect
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




























class Advisor1():
    async def greeting_msg(self):
        greeting_instruction= {"role": "system", "content":  "ask the user want he wants to search for"}
            #"You are a helpful assistant. Say Hello to the user, Introduce yourself. Describe the app. Describe how you would like to help him and what the next steps are that you have planned. You need to access the vector DB in the next steps to find outfits and shopping items. the user needs to provide personal data."}
        msg=[instruction_message,greeting_instruction]
        print("...........................................")
        user_input=await self.session.compl_send_await(msg,model="openrouter_gpt35",method_response="request", args={"max_tokens": 150,"temperature": 0.7,"max_recursion_depth": 10})
        print("...........................................")
        print(user_input)
        return user_input    
    
    def __init__(self,session,mcp,websocket,manager,session_id):
        """
        Initialize the Advisor1 instance.

        Parameters
        ----------
        session : Session
            The session object that is used to communicate with the user.
        mcp : ModelContextProtocol
            The ModelContextProtocol object that is used to communicate with the models.
        websocket : WebSocket
            The websocket object that is used to communicate with the user.
        manager : Manager
            The Manager object that is used to manage the sessions.
        session_id : str
            The session id of the user.

        Returns
        -------
        None
        """
        self.session = session
        self.mcp = mcp
        self.websocket = websocket
        self.manager = manager
        self.session_id = session_id
        user=asyncio.create_task(self.greeting_msg())
        print(user)
        
     
	
    
        