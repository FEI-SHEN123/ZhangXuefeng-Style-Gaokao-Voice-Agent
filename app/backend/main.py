import base64
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .services.agent import generate_reply
from .services.asr import transcribe_upload
from .services.tts import synthesize_speech


load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = REPO_ROOT / "app" / "frontend"

app = FastAPI(title="Zhang-style Voice Advisor MVP")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


class ChatRequest(BaseModel):
    text: str
    history: list[dict[str, str]] = []


class ChatResponse(BaseModel):
    transcript: str
    reply: str
    audio_base64: str | None = None
    audio_mime: str | None = "audio/wav"
    audio_fallback: str | None = None


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    try:
        reply = generate_reply(REPO_ROOT, text, payload.history)
        audio = synthesize_speech(reply)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(
        transcript=text,
        reply=reply,
        audio_base64=base64.b64encode(audio).decode("ascii"),
        audio_mime="audio/wav",
        audio_fallback=None,
    )


@app.post("/api/voice-chat", response_model=ChatResponse)
async def voice_chat(
    audio: UploadFile = File(...),
    history_json: str = Form("[]"),
) -> ChatResponse:
    import json

    try:
        history: Any = json.loads(history_json)
        if not isinstance(history, list):
            history = []
    except json.JSONDecodeError:
        history = []

    try:
        transcript = await transcribe_upload(audio)
        if not transcript:
            raise HTTPException(status_code=400, detail="No speech was transcribed.")
        reply = generate_reply(REPO_ROOT, transcript, history)
        speech = synthesize_speech(reply)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(
        transcript=transcript,
        reply=reply,
        audio_base64=base64.b64encode(speech).decode("ascii"),
        audio_mime="audio/wav",
    )
