"""Simple, honest message router for StudyPal M2.

Classifies an incoming message into a tier ("cheap" | "mid" | "strong") by a
keyword/length rule -- a real system would classify intent here (e.g. an
intent-classification model or embeddings-based similarity search). This is
deliberately simple and readable for the demo.
"""

import os

from dotenv import load_dotenv

load_dotenv()

STRONG_KEYWORDS = (
    "quiz",
    "test me",
    "generate",
    "grade",
    "evaluate",
    "judge",
    "problem set",
)

MID_KEYWORDS = (
    "explain",
    "why",
    "how",
    "what is",
    "walk me through",
    "example",
)

MID_LENGTH_THRESHOLD = 200

TIER_MODELS = {
    "cheap": os.getenv("MODEL_CHEAP", "meta-llama/llama-3.1-8b-instruct"),
    "mid": os.getenv("MODEL_MID", "google/gemini-2.5-flash"),
    "strong": os.getenv("MODEL_STRONG", "anthropic/claude-sonnet-4.5"),
}


def route(message: str) -> str:
    """Classify a message into "cheap" | "mid" | "strong".

    A real system would classify intent here (e.g. a trained classifier or an
    LLM-based router). This demo uses a simple, honest keyword/length rule.
    """
    text = (message or "").lower()

    if any(keyword in text for keyword in STRONG_KEYWORDS):
        return "strong"

    if len(text) > MID_LENGTH_THRESHOLD:
        return "mid"

    if any(keyword in text for keyword in MID_KEYWORDS):
        return "mid"

    return "cheap"


def model_for(tier: str) -> str:
    """Return the configured model slug for a routing tier."""
    return TIER_MODELS[tier]
