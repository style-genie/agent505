import logging
import os
import dotenv
from typing import Dict, List, Optional
from Agent505.src.session import Session
from Agent505.src.server import start

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

if __name__ == "__main__":
    start()

