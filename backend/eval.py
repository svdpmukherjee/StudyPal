"""StudyPal M6 judge subagent.

A single-purpose subagent: judge the *last* assistant answer against the
question it answered, using an LLM-as-judge on the strong tier (one
deliberate call, not per-turn). Returns a normalized verdict dict and never
crashes on a parse failure -- it returns a safe default verdict instead.
"""

import json
import re

from openrouter import chat_completion
from router import model_for

JUDGE_PROMPT = (
    "You are a strict but fair grader. Judge the assistant's ANSWER to the "
    "student's QUESTION on a 1-5 scale for overall quality, plus accuracy "
    "and clarity (1-5 each), and give a one-sentence plain-text rationale. "
    'Return ONLY a JSON object: {"score":n,"accuracy":n,"clarity":n,'
    '"rationale":"..."}.'
)

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)
_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)

_DEFAULT_VERDICT = {
    "score": 3,
    "accuracy": 3,
    "clarity": 3,
    "rationale": "No rationale returned.",
}


def _clamp_score(value) -> int:
    """Coerce a value to an int clamped to 1..5, defaulting to 3 on garbage."""
    try:
        score = int(value)
    except (TypeError, ValueError):
        return 3
    return max(1, min(5, score))


def _parse_verdict(raw: str) -> dict:
    """Robustly parse a model reply into a normalized verdict dict.

    Tolerates a JSON object wrapped in a code fence and/or prose. On any
    failure to find/parse a JSON object, returns the safe default verdict
    rather than raising.
    """
    if not raw:
        return dict(_DEFAULT_VERDICT)

    candidate = raw.strip()

    fence_match = _FENCE_RE.search(candidate)
    if fence_match:
        candidate = fence_match.group(1).strip()

    object_match = _OBJECT_RE.search(candidate)
    if object_match:
        candidate = object_match.group(0)

    try:
        parsed = json.loads(candidate)
    except (ValueError, TypeError):
        return dict(_DEFAULT_VERDICT)

    if not isinstance(parsed, dict):
        return dict(_DEFAULT_VERDICT)

    rationale = parsed.get("rationale")
    rationale = rationale.strip() if isinstance(rationale, str) and rationale.strip() else "No rationale returned."

    return {
        "score": _clamp_score(parsed.get("score")),
        "accuracy": _clamp_score(parsed.get("accuracy")),
        "clarity": _clamp_score(parsed.get("clarity")),
        "rationale": rationale,
    }


def evaluate_answer(question: str, answer: str) -> dict:
    """Call the strong-tier model to judge the last Q&A pair.

    Returns a normalized verdict dict:
    { "score": int(1..5), "accuracy": int(1..5), "clarity": int(1..5),
    "rationale": str }. Raises `OpenRouterError` (propagated from
    `chat_completion`) on an upstream failure -- callers turn that into a
    clean HTTP 502. A malformed model reply never raises; it yields the
    safe default verdict instead.
    """
    context = [
        {"role": "system", "content": JUDGE_PROMPT},
        {
            "role": "user",
            "content": f"QUESTION:\n{question}\n\nANSWER:\n{answer}",
        },
    ]

    reply = chat_completion(context, model_for("strong"))
    return _parse_verdict(reply)
