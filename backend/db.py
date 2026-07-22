"""MongoDB access for StudyPal.

Exposes the `messages` collection (episodic memory) and a small helper to
persist a chat turn, plus the `profile` collection (durable learner facts,
M3) with helpers to read and add facts. Works against local MongoDB or
Atlas (mongodb+srv), since the client always passes an explicit CA bundle
via certifi.
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
profile = db["profile"]

PROFILE_ID = "learner"


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


def get_profile_facts() -> list[str]:
    """Return the learner's durable facts, or [] if no profile doc exists."""
    doc = profile.find_one({"_id": PROFILE_ID})
    if not doc:
        return []
    return doc.get("facts", [])


def get_recent_messages(limit: int = 20) -> list[dict]:
    """Return the last `limit` chat turns, oldest -> newest, as {role, text}.

    Returns [] when the `messages` collection is empty. Used by the M5
    summarizer subagent to read recent conversation context.
    """
    docs = list(
        messages.find({}, {"role": 1, "text": 1})
        .sort([("ts", -1), ("_id", -1)])
        .limit(limit)
    )
    docs.reverse()
    return [{"role": d["role"], "text": d["text"]} for d in docs]


def get_last_qa() -> dict | None:
    """Return the most recent assistant answer paired with the user question
    that immediately preceded it, as { "question": ..., "answer": ... }.

    Returns None if there is no assistant turn yet (or no user turn before
    it). Used by the M6 eval subagent to judge the last answer. Reuses the
    existing client.
    """
    docs = list(
        messages.find({}, {"role": 1, "text": 1}).sort([("ts", -1), ("_id", -1)])
    )

    answer = None
    for i, doc in enumerate(docs):
        if doc.get("role") == "assistant":
            answer = doc
            rest = docs[i + 1 :]
            for prev in rest:
                if prev.get("role") == "user":
                    return {"question": prev.get("text", ""), "answer": answer.get("text", "")}
            return None
    return None


def add_profile_fact(fact: str) -> list[str]:
    """Trim + add a fact (case-insensitive dedup) and return the full list.

    Blank/whitespace-only facts are ignored (no-op). Uses $addToSet against
    the existing facts (case-insensitive comparison against current values)
    so re-adding the same fact in a different case does not duplicate it.
    """
    fact = fact.strip()
    if not fact:
        return get_profile_facts()

    existing = get_profile_facts()
    if fact.lower() in {f.lower() for f in existing}:
        return existing

    profile.update_one(
        {"_id": PROFILE_ID},
        {
            "$addToSet": {"facts": fact},
            "$set": {"updated_ts": datetime.now(timezone.utc)},
        },
        upsert=True,
    )
    return get_profile_facts()
