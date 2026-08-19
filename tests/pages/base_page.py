"""Base page object — all page objects inherit from this."""
from __future__ import annotations

from playwright.sync_api import Page, expect


class BasePage:
    def __init__(self, page: Page) -> None:
        self.page = page

    # --- Navigation ---

    def navigate(self, url: str) -> None:
        self.page.goto(url)

    def reload(self) -> None:
        self.page.reload()

    def go_back(self) -> None:
        self.page.go_back()

    # --- Current state ---

    @property
    def title(self) -> str:
        return self.page.title()

    @property
    def url(self) -> str:
        return self.page.url

    # --- Interaction helpers ---

    def click(self, selector: str) -> None:
        self.page.click(selector)

    def fill(self, selector: str, value: str) -> None:
        self.page.fill(selector, value)

    def select_option(self, selector: str, value: str) -> None:
        self.page.select_option(selector, value)

    def get_text(self, selector: str) -> str:
        return self.page.text_content(selector) or ""

    # --- Wait helpers ---

    def wait_for_url(self, pattern: str, timeout: int = 10_000) -> None:
        self.page.wait_for_url(pattern, timeout=timeout)

    def wait_for_selector(self, selector: str, timeout: int = 10_000):
        return self.page.wait_for_selector(selector, timeout=timeout)

    def wait_for_load(self) -> None:
        self.page.wait_for_load_state("networkidle")

    # --- Assertion shortcuts ---

    def expect_url_contains(self, fragment: str) -> None:
        expect(self.page).to_have_url(f".*{fragment}.*")

    def expect_title_contains(self, text: str) -> None:
        expect(self.page).to_have_title(f".*{text}.*")

    def expect_visible(self, selector: str) -> None:
        expect(self.page.locator(selector)).to_be_visible()

    def expect_text(self, selector: str, text: str) -> None:
        expect(self.page.locator(selector)).to_have_text(text)

    # --- Screenshot ---

    def screenshot(self, path: str) -> None:
        self.page.screenshot(path=path, full_page=True)
