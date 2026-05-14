import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv


ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/customization"
TARGET_MODEL = "cosyvoice-v3.5-flash"


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def post_json(url: str, api_key: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"DashScope voice clone request failed: HTTP {exc.code}\n{error_body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"DashScope voice clone request failed: {exc}") from exc


def main() -> int:
    load_dotenv(Path(".env"))

    api_key = require_env("DASHSCOPE_API_KEY")
    audio_url = require_env("VOICE_CLONE_AUDIO_URL")
    prefix = os.getenv("VOICE_CLONE_PREFIX", "myvoice").strip() or "myvoice"

    payload = {
        "model": "voice-enrollment",
        "input": {
            "action": "create_voice",
            "target_model": TARGET_MODEL,
            "prefix": prefix,
            "url": audio_url,
            "language_hints": ["zh"],
            "max_prompt_audio_length": 30,
            "enable_preprocess": True,
        },
    }

    data = post_json(ENDPOINT, api_key, payload)
    voice_id = data.get("output", {}).get("voice_id")
    if not voice_id:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        raise SystemExit("DashScope did not return output.voice_id.")

    print(f"voice_id={voice_id}")
    print()
    print("Add these lines to .env:")
    print("TTS_PROVIDER=dashscope_cloned")
    print(f"TTS_MODEL={TARGET_MODEL}")
    print(f"TTS_VOICE_ID={voice_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
