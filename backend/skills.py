"""StudyPal M4 skills: allowlisted procedural-memory prompt loader.

Skill prompts live as plain-text/Markdown files under backend/skills/. This
module loads them by name against a fixed allowlist so a caller can never
read an arbitrary file (e.g. "../secrets"), and exposes each skill's
suggested routing tier.
"""

from pathlib import Path

# name -> suggested tier ("mid" | "strong"). This is the single source of
# truth for which skill names are allowed; anything not in this dict is
# rejected before it ever touches the filesystem.
ALLOWED_SKILLS = {
    "explain-simply": "mid",
    "quiz-me": "strong",
}

SKILLS_DIR = Path(__file__).resolve().parent / "skills"


def load_skill(name: str) -> str:
    """Return the prompt text for an allowlisted skill name.

    Raises ValueError for any name not in ALLOWED_SKILLS (unknown or
    path-like names, e.g. "../secrets", are rejected before any file I/O).
    """
    if name not in ALLOWED_SKILLS:
        raise ValueError(f"Unknown skill: {name!r}")

    path = SKILLS_DIR / f"{name}.md"
    return path.read_text(encoding="utf-8").strip()


def skill_tier(name: str) -> str:
    """Return the suggested routing tier for an allowlisted skill name."""
    if name not in ALLOWED_SKILLS:
        raise ValueError(f"Unknown skill: {name!r}")

    return ALLOWED_SKILLS[name]
