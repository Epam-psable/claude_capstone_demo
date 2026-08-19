import pytest
from pathlib import Path

from sync_engine.config_manager import ConfigManager
from sync_engine.exceptions import ConfigurationError


def test_load_valid_config(sync_rules_yaml, repo_root):
    cfg = ConfigManager(sync_rules_yaml).load()
    assert cfg.source_extensions == [".py"]
    assert cfg.docs_root == Path("docs")


def test_missing_config_file(repo_root):
    with pytest.raises(ConfigurationError, match="not found"):
        ConfigManager(repo_root / "nonexistent.yaml").load()


def test_missing_docs_root_field(repo_root):
    bad = repo_root / "bad.yaml"
    bad.write_text("source_extensions:\n  - .py\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="docs_root"):
        ConfigManager(bad).load()


def test_missing_source_extensions_field(repo_root):
    bad = repo_root / "bad.yaml"
    bad.write_text("docs_root: docs\n", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="source_extensions"):
        ConfigManager(bad).load()


def test_empty_config_file(repo_root):
    empty = repo_root / "empty.yaml"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="empty"):
        ConfigManager(empty).load()


def test_invalid_yaml(repo_root):
    bad = repo_root / "bad.yaml"
    bad.write_text("key: [unclosed", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="invalid YAML"):
        ConfigManager(bad).load()
