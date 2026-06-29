import config
import pytest


def reload_config(monkeypatch, tmp_path, *, version=None, prompt_path=None):
    prompts_dir = tmp_path / "config" / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(config, "BASE_DIR", tmp_path)
    monkeypatch.setattr(config, "PROMPTS_DIR", prompts_dir)
    if version is None:
        monkeypatch.delenv("SYSTEM_PROMPT_VERSION", raising=False)
    else:
        monkeypatch.setenv("SYSTEM_PROMPT_VERSION", version)
    if prompt_path is None:
        monkeypatch.delenv("SYSTEM_PROMPT_PATH", raising=False)
    else:
        monkeypatch.setenv("SYSTEM_PROMPT_PATH", prompt_path)
    return config._resolve_system_prompt()


def test_system_prompt_resolves_versioned_file(monkeypatch, tmp_path):
    versioned = tmp_path / "config" / "prompts" / "systemprompt-0.0.2.md"
    versioned.parent.mkdir(parents=True)
    versioned.write_text("v2", encoding="utf-8")

    path, version = reload_config(monkeypatch, tmp_path, version="0.0.2")

    assert path == versioned
    assert version == "0.0.2"


def test_system_prompt_path_overrides_version(monkeypatch, tmp_path):
    custom = tmp_path / "custom_prompt.md"
    custom.write_text("custom", encoding="utf-8")

    path, version = reload_config(
        monkeypatch,
        tmp_path,
        version="0.0.2",
        prompt_path=str(custom),
    )

    assert path == custom
    assert version == "0.0.2"


def test_system_prompt_missing_version_fails(monkeypatch, tmp_path):
    with pytest.raises(FileNotFoundError, match="system prompt versionado"):
        reload_config(monkeypatch, tmp_path, version="9.9.9")
