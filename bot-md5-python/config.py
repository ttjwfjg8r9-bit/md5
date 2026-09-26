import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("MD5_API_TOKEN", "")
API_URL = os.getenv(
    "MD5_API_URL",
    "https://md5.changdelamgica.xyz/api/GetListSoiCau",
)
PORT = int(os.getenv("PORT", 8000))
MAX_HISTORY = int(os.getenv("MAX_HISTORY", 2000))
WARMUP_ROUNDS = int(os.getenv("WARMUP_ROUNDS", 10))
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", 8))
AUTO_GIT_PUSH = os.getenv("AUTO_GIT_PUSH", "false").lower() == "true"
