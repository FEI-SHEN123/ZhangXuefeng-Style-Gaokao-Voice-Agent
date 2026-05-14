from openai import OpenAI

from .config import get_settings


def get_openai_client() -> OpenAI:
    settings = get_settings()
    if not settings.has_openai_audio_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Copy .env.example to .env and fill it in.")
    return OpenAI(api_key=settings.openai_api_key)


def get_llm_client() -> OpenAI:
    settings = get_settings()
    if not settings.llm_api_key:
        raise RuntimeError(
            "LLM_API_KEY or DASHSCOPE_API_KEY is not set. "
            "Copy .env.example to .env and fill in your Qwen/DashScope API key."
        )
    return OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
