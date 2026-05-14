from http import HTTPStatus
from pathlib import Path
from uuid import uuid4
import wave

from fastapi import UploadFile
import dashscope
from dashscope.audio.asr import Recognition

from .config import get_settings


def _extract_text(sentence: object) -> str:
    if isinstance(sentence, str):
        return sentence.strip()

    if isinstance(sentence, dict):
        value = sentence.get("text") or sentence.get("sentence") or sentence.get("transcript")
        return str(value or "").strip()

    if isinstance(sentence, list):
        parts = [_extract_text(item) for item in sentence]
        return "".join(part for part in parts if part).strip()

    return ""


def _wav_sample_rate(path: Path) -> int:
    with wave.open(str(path), "rb") as wav_file:
        return wav_file.getframerate()


async def transcribe_upload(file: UploadFile) -> str:
    settings = get_settings()
    if settings.asr_provider != "dashscope":
        raise RuntimeError(f"Unsupported ASR_PROVIDER: {settings.asr_provider}")
    if not settings.has_dashscope_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not set.")
    if "realtime" not in settings.asr_model:
        raise RuntimeError(
            f"{settings.asr_model} is a file transcription model. "
            "This MVP uses browser-uploaded local audio with DashScope Recognition, "
            "so set ASR_MODEL=paraformer-realtime-8k-v2, or add OSS upload support for paraformer-v2."
        )

    dashscope.api_key = settings.dashscope_api_key

    audio_bytes = await file.read()
    runtime_dir = Path(".runtime") / "audio"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    wav_path = runtime_dir / f"{uuid4().hex}.wav"
    wav_path.write_bytes(audio_bytes)

    try:
        sample_rate = _wav_sample_rate(wav_path)
        recognition = Recognition(
            model=settings.asr_model,
            format="wav",
            sample_rate=sample_rate,
            language_hints=["zh", "en"],
            callback=None,
        )
        result = recognition.call(str(wav_path))
    finally:
        wav_path.unlink(missing_ok=True)

    if result.status_code != HTTPStatus.OK:
        raise RuntimeError(f"DashScope ASR failed: {getattr(result, 'message', result)}")

    return _extract_text(result.get_sentence())
