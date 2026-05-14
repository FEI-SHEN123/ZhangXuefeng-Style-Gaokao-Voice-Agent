from pathlib import Path

from .config import get_settings
from .openai_client import get_llm_client
from .prompt_loader import load_system_prompt


def generate_reply(repo_root: Path, user_text: str, history: list[dict[str, str]] | None = None) -> str:
    settings = get_settings()
    client = get_llm_client()
    system_prompt = load_system_prompt(repo_root, settings.skill_path)

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
    ]

    for item in history or []:
        role = item.get("role")
        content = item.get("content")
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_text})

    completion = client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=0.75,
    )

    content = completion.choices[0].message.content
    return (content or "").strip()
