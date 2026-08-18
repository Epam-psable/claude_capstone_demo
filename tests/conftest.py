"""Shared pytest fixtures for sync engine tests."""

import os

import pytest
from pathlib import Path

# ---------------------------------------------------------------------------
# Playwright fixtures (only active when playwright is installed and e2e mark used)
# ---------------------------------------------------------------------------

try:
    from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright
    _playwright_available = True
except ImportError:
    _playwright_available = False


@pytest.fixture(scope="session")
def playwright_instance():
    if not _playwright_available:
        pytest.skip("playwright not installed")
    with sync_playwright() as pw:
        yield pw


@pytest.fixture(scope="session")
def browser(playwright_instance):
    headless = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() != "false"
    br = playwright_instance.chromium.launch(headless=headless)
    yield br
    br.close()


@pytest.fixture(scope="function")
def browser_context(browser):
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True,
    )
    yield ctx
    ctx.close()


@pytest.fixture(scope="function")
def page(browser_context):
    p = browser_context.new_page()
    yield p
    p.close()


@pytest.fixture(scope="function")
def sync_report_page(page):
    from tests.pages import SyncReportPage
    base_url = os.getenv("REPORT_BASE_URL", "http://localhost:8080")
    return SyncReportPage(page, base_url)


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
