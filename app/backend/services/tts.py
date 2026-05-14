import dashscope
from dashscope.audio.tts import SpeechSynthesizer
from dashscope.audio.tts_v2 import SpeechSynthesizer as CosyVoiceSynthesizer

from .config import get_settings


def synthesize_speech(text: str) -> bytes:
    settings = get_settings()
    if not settings.has_dashscope_key:
        raise RuntimeError("DASHSCOPE_API_KEY is not set.")

    if settings.tts_provider == "dashscope":
        return _synthesize_sambert(text)

    if settings.tts_provider == "dashscope_cloned":
        return _synthesize_cloned_voice(text)

    raise RuntimeError(f"Unsupported TTS_PROVIDER: {settings.tts_provider}")


def _synthesize_sambert(text: str) -> bytes:
    settings = get_settings()
    dashscope.api_key = settings.dashscope_api_key
    dashscope.base_websocket_api_url = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"

    result = SpeechSynthesizer.call(
        model=settings.tts_model_domestic,
        text=text,
        format="wav",
        sample_rate=16000,
        volume=50,
        rate=1.12,
        pitch=0.95,
    )

    audio = result.get_audio_data()
    if audio:
        return bytes(audio)

    response = result.get_response()
    raise RuntimeError(f"DashScope TTS returned no audio: {response}")


def _synthesize_cloned_voice(text: str) -> bytes:
    settings = get_settings()
    if not settings.tts_voice_id:
        raise RuntimeError(
            "TTS_PROVIDER=dashscope_cloned requires TTS_VOICE_ID. "
            "Run scripts/create_dashscope_voice.py first, then put the returned voice_id in .env."
        )

    dashscope.api_key = settings.dashscope_api_key
    dashscope.base_websocket_api_url = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"

    synthesizer = CosyVoiceSynthesizer(
        model=settings.tts_model_domestic,
        voice=settings.tts_voice_id,
    )
    audio = synthesizer.call(text)
    if audio:
        return bytes(audio)

    raise RuntimeError(
        "DashScope cloned voice TTS returned no audio "
        f"(model={settings.tts_model_domestic}, voice_id={settings.tts_voice_id})."
    )
