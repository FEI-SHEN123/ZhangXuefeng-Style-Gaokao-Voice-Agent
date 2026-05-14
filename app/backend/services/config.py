from functools import lru_cache
from pathlib import Path
from pydantic import BaseModel
import os


class Settings(BaseModel):
    openai_api_key: str | None = None
    dashscope_api_key: str | None = None
    llm_api_key: str | None = None
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen3.5-flash"
    asr_provider: str = "dashscope"
    asr_model: str = "paraformer-realtime-8k-v2"
    tts_provider: str = "dashscope"
    tts_model_domestic: str = "sambert-zhida-v1"
    tts_voice_domestic: str = "sambert-zhida-v1"
    tts_voice_id: str | None = None
    voice_clone_audio_url: str | None = None
    voice_clone_prefix: str = "myvoice"
    transcribe_model: str = "gpt-4o-mini-transcribe"
    tts_model: str = "gpt-4o-mini-tts"
    tts_voice: str = "ash"
    skill_path: Path = Path("SKILL.md")

    @property
    def has_openai_audio_key(self) -> bool:
        return bool(
            self.openai_api_key
            and self.openai_api_key.strip()
            and "your-key" not in self.openai_api_key
            and "your_openai" not in self.openai_api_key.lower()
        )

    @property
    def has_dashscope_key(self) -> bool:
        return bool(
            self.dashscope_api_key
            and self.dashscope_api_key.strip()
            and "your-dashscope" not in self.dashscope_api_key
        )


@lru_cache
def get_settings() -> Settings:
    dashscope_api_key = os.getenv("DASHSCOPE_API_KEY")
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        dashscope_api_key=dashscope_api_key,
        llm_api_key=(
            os.getenv("LLM_API_KEY")
            or dashscope_api_key
            or os.getenv("OPENAI_API_KEY")
        ),
        llm_base_url=os.getenv(
            "LLM_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ),
        llm_model=os.getenv("LLM_MODEL", os.getenv("OPENAI_CHAT_MODEL", "qwen3.5-flash")),
        asr_provider=os.getenv("ASR_PROVIDER", "dashscope"),
        asr_model=os.getenv("ASR_MODEL", "paraformer-realtime-8k-v2"),
        tts_provider=os.getenv("TTS_PROVIDER", "dashscope"),
        tts_model_domestic=os.getenv("TTS_MODEL", "sambert-zhida-v1"),
        tts_voice_domestic=os.getenv("TTS_VOICE", "sambert-zhida-v1"),
        tts_voice_id=os.getenv("TTS_VOICE_ID"),
        voice_clone_audio_url=os.getenv("VOICE_CLONE_AUDIO_URL"),
        voice_clone_prefix=os.getenv("VOICE_CLONE_PREFIX", "myvoice"),
        transcribe_model=os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe"),
        tts_model=os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts"),
        tts_voice=os.getenv("OPENAI_TTS_VOICE", "ash"),
        skill_path=Path(os.getenv("ZHANG_SKILL_PATH", "SKILL.md")),
    )
