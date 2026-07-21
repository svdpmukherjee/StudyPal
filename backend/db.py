"""MongoDB access for StudyPal.

Exposes the `messages` collection (episodic memory) and a small helper to
persist a chat turn. Works against local MongoDB or Atlas (mongodb+srv),
since the client always passes an explicit CA bundle via certifi.
"""

import os
from datetime import datetime, timezone

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "studypal")

# tlsCAFile is ignored on a plain (non-TLS) local connection, so this is safe
# for local Mongo and required for Atlas (mongodb+srv) on macOS.
client = MongoClient(MONGODB_URI, tlsCAFile=certifi.where())
db = client[MONGODB_DB]
messages = db["messages"]


def save_message(role: str, text: str):
    """Persist one chat turn as { role, text, ts } and return the doc."""
    doc = {
        "role": role,
        "text": text,
        "ts": datetime.now(timezone.utc),
    }
    result = messages.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc
