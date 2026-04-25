"""Mongo client + tiny helpers shared across routes."""
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

from .config import MONGO_URL, DB_NAME

client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return uuid.uuid4().hex


def sanitize(doc: dict) -> dict:
    """Strip Mongo's internal _id from a document so it can be JSON-serialised.
    Use on every document returned to the client (see top-level rules)."""
    if not isinstance(doc, dict):
        return doc
    out = {k: v for k, v in doc.items() if k != "_id"}
    return out
