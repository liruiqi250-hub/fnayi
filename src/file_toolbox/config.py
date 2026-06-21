from dataclasses import dataclass
from pathlib import Path
import sys

from dotenv import dotenv_values


class ConfigError(RuntimeError):
    """User-facing configuration error."""


@dataclass(frozen=True)
class AppConfig:
    api_key: str
    base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-v4-pro"


def _default_env_path() -> Path:
    executable_dir = Path(sys.executable).resolve().parent
    candidates = [
        Path.cwd() / ".env",
        executable_dir / ".env",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path.cwd() / ".env"


def load_config(env_path: Path | str | None = None) -> AppConfig:
    values = dotenv_values(env_path or _default_env_path())
    api_key = (values.get("DEEPSEEK_API_KEY") or "").strip()
    base_url = (values.get("DEEPSEEK_BASE_URL") or "https://api.deepseek.com").strip()
    model = (values.get("DEEPSEEK_MODEL") or "deepseek-v4-pro").strip()

    if not api_key:
        raise ConfigError("请在 .env 文件中配置 DEEPSEEK_API_KEY")

    return AppConfig(api_key=api_key, base_url=base_url, model=model)
