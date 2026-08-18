"""Playwright fixtures for E2E tests."""
from __future__ import annotations

import os

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from tests.pages import ConfluencePage, GitHubPRPage


# ---------------------------------------------------------------------------
# Browser lifecycle
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as pw:
        yield pw


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Browser:
    headless = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() != "false"
    br = playwright_instance.chromium.launch(headless=headless)
    yield br
    br.close()


@pytest.fixture(scope="function")
def context(browser: Browser) -> BrowserContext:
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True,
    )
    yield ctx
    ctx.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Page:
    p = context.new_page()
    yield p
    p.close()


# ---------------------------------------------------------------------------
# Page-object factories
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def github_pr_page(page: Page) -> GitHubPRPage:
    repo = os.getenv("GITHUB_REPO", "Epam-psable/claude_capstone_demo")
    return GitHubPRPage(page, repo)


@pytest.fixture(scope="function")
def confluence_page(page: Page) -> ConfluencePage:
    return ConfluencePage(page)


# ---------------------------------------------------------------------------
# Auth helpers (stored in env, never committed)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def confluence_credentials() -> dict[str, str]:
    return {
        "email": os.getenv("CONFLUENCE_EMAIL", ""),
        "password": os.getenv("CONFLUENCE_API_TOKEN", ""),
    }
