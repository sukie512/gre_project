"""
database.py — MongoDB Atlas singleton.
Shared across the entire app via module-level variables.
"""
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI", "")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI not set. Copy .env.example → .env and fill it in.")

_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
_db     = _client["gre_prep"]

questions_col = _db["questions"]
sessions_col  = _db["userSessions"]


def ping() -> bool:
    """Return True if Atlas is reachable."""
    try:
        _client.admin.command("ping")
        return True
    except Exception:
        return False
