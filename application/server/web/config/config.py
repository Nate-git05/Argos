import os  # standard lib for reading environment variables
from pathlib import Path  # used to build an absolute path to the .env file

from dotenv import load_dotenv  # loads key=value pairs from .env into the process environment

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"  # server/web/.env, next to app.py

load_dotenv(ENV_PATH)  # populate os.environ from the .env file

POSTGRES_URI = os.getenv("POSTGRES_URI")  # read the connection string into memory
if not POSTGRES_URI:
    raise ValueError("POSTGRES_URI is not set in server/web/.env")  # fail loudly at import time, not on first query
