import logging
import os
import dotenv
from typing import Dict, List, Optional
from src.session import Session
from src.server import ConnectionManager

#   --------> LOGGER <--------
logging.basicConfig(
    format="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    datefmt="%Y-%m-%d:%H:%M:%S",
    level=logging.DEBUG,
    )
logger = logging.getLogger(__name__)
# --------> Load environment variables <--------
dotenv.load_dotenv("./.env.local")
class Agent505:
    def __init__(self):
        self.sessions={}
        self.websocket_manager=ConnectionManager()
    async def start_session(self,websocket,session_id):
        session = Session(self.websocket_manager,websocket,session_id)
        self.sessions[session_id]={
            "websocket":websocket,
            "session":session,
            "session_id":session_id
        }
        
        
        
