"""StudyPal M5 summarizer subagent.

A single-purpose subagent: read recent chat turns and extract candidate
durable facts about the *learner* (topic, weak spots, stated preferences).
Uses the strong tier (a one-off, deliberate call, not per-turn) and returns a
plain list of short strings, tolerating a model that doesn't return clean
JSON. Never crashes on a parse failure -- it returns [] instead.
"""

import json
import re

from openrouter import chat_completion
from router import model_for

EXTRACTOR_PROMPT = (
    "You are a summarizer. Read the conversation below and extract at most "
    "5 short, durable facts about the *learner* -- what they're studying, "
    "weak spots, stated preferences. Do not include facts about the world "
    "or general knowledge, only facts about this specific learner.\n\n"
    "Return ONLY a JSON array of short strings, nothing else. "
    'Return [] if there is nothing durable to remember, e.g. ["studying '
    'recursion", "weak on binary trees"].'
)

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)


def _render_transcript(messages: list[dict]) -> str:
    lines = [f"{m.get('role', 'user')}: {m.get('text', '')}" for m in messages]
    return "\n".join(lines)


def _parse_facts(raw: str) -> list[str]:
    """Robustly parse a model reply into a list of trimmed, non-empty strings.

    Tolerates a JSON array wrapped in a code fence and/or prose. On any
    failure to find/parse a JSON array, returns [] rather than raising.
    """
    if not raw:
        return []

    candidate = raw.strip()

    fence_match = _FENCE_RE.search(candidate)
    if fence_match:
        candidate = fence_match.group(1).strip()

    array_match = _ARRAY_RE.search(candidate)
    if array_match:
        candidate = array_match.group(0)

    try:
        parsed = json.loads(candidate)
    except (ValueError, TypeError):
        return []

    if not isinstance(parsed, list):
        return []

    facts = []
    for item in parsed:
        if isinstance(item, str):
            trimmed = item.strip()
            if trimmed:
                facts.append(trimmed)
    return facts


def summarize_messages(messages: list[dict]) -> list[str]:
    """Call the strong-tier model to extract candidate durable facts.

    `messages` is a list of {"role", "text"} dicts (oldest -> newest).
    Returns a list of short strings (possibly empty). Raises
    `OpenRouterError` (propagated from `chat_completion`) on an upstream
    failure -- callers turn that into a clean HTTP 502.
    """
    transcript = _render_transcript(messages)
    context = [
        {"role": "system", "content": EXTRACTOR_PROMPT},
        {"role": "user", "content": transcript},
    ]

    reply = chat_completion(context, model_for("strong"))
    return _parse_facts(reply)
