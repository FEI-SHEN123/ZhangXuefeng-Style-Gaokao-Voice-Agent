from pathlib import Path


def load_system_prompt(repo_root: Path, skill_path: Path) -> str:
    wrapper_path = repo_root / "app" / "backend" / "prompts" / "system_wrapper.md"
    wrapper = wrapper_path.read_text(encoding="utf-8")

    resolved_skill_path = skill_path
    if not resolved_skill_path.is_absolute():
        resolved_skill_path = repo_root / resolved_skill_path

    skill = resolved_skill_path.read_text(encoding="utf-8")
    return f"{wrapper}{skill}"
