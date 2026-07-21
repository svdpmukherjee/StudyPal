"""StudyPal FastAPI backend - M1 chat core + M2 model routing + M3 memory.

POST /chat: save the user message, load durable profile facts and inject
them into the system prompt, route to a tier (cheap/mid/strong), call
OpenRouter with the tier's model, save the assistant reply, return
reply + tier + model.

GET/POST /profile: read/append durable learner facts (M3 memory). Skills
(M4) and automatic distillation (M5) are not implemented here.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo.errors import PyMongoError

from db import add_profile_fact, get_profile_facts, save_message
from openrouter import OpenRouterError, chat_completion
from router import model_for, route

app = FastAPI(title="StudyPal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = (
    "You are StudyPal, a friendly, encouraging study buddy. Explain things "
    "clearly and use Markdown (headings, lists, code blocks) when it helps."
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    tier: str
    model: str


class ProfileResponse(BaseModel):
    facts: list[str]


class ProfileFactRequest(BaseModel):
    fact: str


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/profile", response_model=ProfileResponse)
def get_profile():
    try:
        return {"facts": get_profile_facts()}
    except PyMongoError as exc:
        raise HTTPException(status_code=502, detail=f"Profile store error: {exc}") from exc


@app.post("/profile", response_model=ProfileResponse)
def post_profile(req: ProfileFactRequest):
    fact = req.fact.strip()
    if not fact:
        raise HTTPException(status_code=400, detail="fact must not be empty")

    try:
        facts = add_profile_fact(fact)
    except PyMongoError as exc:
        raise HTTPException(status_code=502, detail=f"Profile store error: {exc}") from exc

    return {"facts": facts}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    save_message("user", req.message)

    tier = route(req.message)
    model = model_for(tier)

    system_prompt = SYSTEM_PROMPT
    try:
        facts = get_profile_facts()
    except PyMongoError:
        facts = []

    if facts:
        facts_block = "\n".join(f"- {f}" for f in facts)
        system_prompt += (
            "\n\nWhat you already know about this learner:\n"
            f"{facts_block}\n"
            "Use this to feel like you remember them and gently revisit "
            "weak spots."
        )

    context = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": req.message},
    ]

    try:
        reply = chat_completion(context, model)
    except OpenRouterError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    save_message("assistant", reply)

    return {"reply": reply, "tier": tier, "model": model}
