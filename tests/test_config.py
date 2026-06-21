from pathlib import Path

import pytest

from file_toolbox.config import AppConfig, ConfigError, load_config


def test_load_config_reads_deepseek_values(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DEEPSEEK_API_KEY=sk-test\n"
        "DEEPSEEK_BASE_URL=https://api.deepseek.com\n"
        "DEEPSEEK_MODEL=deepseek-v4-pro\n",
        encoding="utf-8",
    )

    config = load_config(env_file)

    assert config == AppConfig(
        api_key="sk-test",
        base_url="https://api.deepseek.com",
        model="deepseek-v4-pro",
    )


def test_load_config_rejects_missing_api_key(tmp_path: Path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DEEPSEEK_BASE_URL=https://api.deepseek.com\n"
        "DEEPSEEK_MODEL=deepseek-v4-pro\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="DEEPSEEK_API_KEY"):
        load_config(env_file)
