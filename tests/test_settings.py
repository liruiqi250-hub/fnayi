from pathlib import Path

import pytest

from file_toolbox.settings import AppSettings, load_settings, save_settings, resolve_api_config


def test_load_settings_returns_defaults_when_no_file():
    settings = load_settings()
    assert isinstance(settings, AppSettings)
    assert settings.api_key == ""


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    import file_toolbox.settings as s
    monkeypatch.setattr(s, "SETTINGS_FILE", tmp_path / "settings.json")
    settings = AppSettings(api_key="sk-test", output_dir="C:\\out")
    save_settings(settings)
    loaded = load_settings()
    assert loaded.api_key == "sk-test"
    assert loaded.output_dir == "C:\\out"
    assert loaded.open_output_after_done is True


def test_resolve_api_config_uses_settings_first():
    settings = AppSettings(api_key="sk-from-settings", base_url="https://custom.api.com")
    config = resolve_api_config(settings)
    assert config.api_key == "sk-from-settings"
    assert config.base_url == "https://custom.api.com"


def test_resolve_api_config_falls_back_to_defaults_with_empty_key(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    settings = AppSettings(api_key="", base_url="")
    config = resolve_api_config(settings)
    assert config.api_key == ""
    assert config.base_url == "https://api.deepseek.com"
