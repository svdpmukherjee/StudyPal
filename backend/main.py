"""StudyPal FastAPI backend - M1 chat core.

One route, POST /chat: save the user message, call OpenRouter with the
single OPENROUTER_MODEL, save the assistant reply, return it. No routing,
memory, or skills yet (those are M2+).
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import save_message
from openrouter import OpenRouterError, chat_completion

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


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    save_message("user", req.message)

    context = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": req.message},
    ]

    try:
        reply = chat_completion(context)
    except OpenRouterError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    save_message("assistant", reply)

    return {"reply": reply}
