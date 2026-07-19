"""Minimal OpenRouter chat-completion client for StudyPal M1.

Single-model call (no routing/tiers yet - that's M2). Raises a clear
`OpenRouterError` on any upstream failure so the caller can turn it into a
clean HTTP 502 instead of an unhandled 500.
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterError(Exception):
    """Raised when OpenRouter cannot fulfil a chat completion request."""


def chat_completion(messages: list[dict]) -> str:
    """Call OpenRouter with the configured OPENROUTER_MODEL.

    `messages` is a list of {"role": ..., "content": ...} dicts.
    Returns the assistant reply text, or raises OpenRouterError.
    """
    if not OPENROUTER_API_KEY:
        raise OpenRouterError("OPENROUTER_API_KEY is not configured")
    if not OPENROUTER_MODEL:
        raise OpenRouterError("OPENROUTER_MODEL is not configured")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"model": OPENROUTER_MODEL, "messages": messages}

    try:
        response = httpx.post(
            OPENROUTER_URL, headers=headers, json=payload, timeout=30.0
        )
    except httpx.TimeoutException as exc:
        raise OpenRouterError("OpenRouter request timed out") from exc
    except httpx.HTTPError as exc:
        raise OpenRouterError(f"OpenRouter request failed: {exc}") from exc

    if response.status_code < 200 or response.status_code >= 300:
        raise OpenRouterError(
            f"OpenRouter returned {response.status_code}: {response.text[:500]}"
        )

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        raise OpenRouterError("OpenRouter response missing content") from exc

    if not content or not content.strip():
        raise OpenRouterError("OpenRouter returned an empty reply")

    return content
