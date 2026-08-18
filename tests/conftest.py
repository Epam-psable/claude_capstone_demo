"""Shared pytest fixtures for sync engine tests."""

import pytest
from pathlib import Path


@pytest.fixture
def repo_root(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def docs_dir(repo_root: Path) -> Path:
    d = repo_root / "docs"
    d.mkdir()
    return d


@pytest.fixture
def src_dir(repo_root: Path) -> Path:
    d = repo_root / "src" / "sync_engine"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def sample_py_old() -> str:
    return """\
def existing_func():
    pass

def to_be_removed():
    pass
"""


@pytest.fixture
def sample_py_new() -> str:
    return """\
def existing_func():
    return 42

def new_func():
    pass
"""


@pytest.fixture
def doc_with_section() -> str:
    return """\
# My Module

Some manual documentation.

## Module Update

*Last synced: 2026-01-01*

Old content here.

## Other Section

More manual content.
"""


@pytest.fixture
def doc_without_section() -> str:
    return """\
# My Module

Some manual documentation — no module update section.

## Other Section

More manual content.
"""


@pytest.fixture
def sync_rules_yaml(repo_root: Path) -> Path:
    config = repo_root / "config"
    config.mkdir()
    rules = config / "sync_rules.yaml"
    rules.write_text(
        "source_extensions:\n  - .py\ndocs_root: docs\n", encoding="utf-8"
    )
    return rules
