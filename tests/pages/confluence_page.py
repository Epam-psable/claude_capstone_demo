"""Page object for Confluence documentation pages (used in Stage 1 verification)."""
from __future__ import annotations

from playwright.sync_api import Page

from .base_page import BasePage


class ConfluencePage(BasePage):
    """Represents a Confluence wiki page."""

    BASE_URL = "https://epam-team-pnqaof71.atlassian.net/wiki"

    # Selectors
    _PAGE_TITLE = "h1[data-testid='page-title']"
    _PAGE_BODY = "div#main-content"
    _BREADCRUMB = "nav[aria-label='breadcrumbs']"
    _SPACE_TITLE = "span.space-name"
    _LAST_MODIFIED = "time[datetime]"
    _LOGIN_EMAIL = "input#username"
    _LOGIN_NEXT = "button#login-submit"
    _LOGIN_PASSWORD = "input#password"
    _LOGIN_SUBMIT = "button#login-submit"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # --- Navigation ---

    def open_page(self, page_id: str) -> None:
        self.navigate(f"{self.BASE_URL}/pages/{page_id}")
        self.wait_for_load()

    def open_space(self, space_key: str) -> None:
        self.navigate(f"{self.BASE_URL}/spaces/{space_key}")
        self.wait_for_load()

    # --- Login ---

    def login(self, email: str, password: str) -> None:
        self.navigate(f"{self.BASE_URL}/login")
        self.fill(self._LOGIN_EMAIL, email)
        self.click(self._LOGIN_NEXT)
        self.wait_for_selector(self._LOGIN_PASSWORD)
        self.fill(self._LOGIN_PASSWORD, password)
        self.click(self._LOGIN_SUBMIT)
        self.wait_for_load()

    # --- Page content ---

    def get_page_title(self) -> str:
        return self.get_text(self._PAGE_TITLE).strip()

    def get_page_body(self) -> str:
        return self.get_text(self._PAGE_BODY).strip()

    def get_last_modified(self) -> str:
        el = self.page.locator(self._LAST_MODIFIED).first
        return el.get_attribute("datetime") or ""

    # --- Assertions ---

    def expect_page_title_contains(self, text: str) -> None:
        title = self.get_page_title()
        assert text in title, f"Expected '{text}' in page title, got: '{title}'"

    def expect_body_contains(self, text: str) -> None:
        body = self.get_page_body()
        assert text in body, f"Expected '{text}' in page body"

    def expect_logged_in(self) -> None:
        self.expect_visible(self._PAGE_BODY)
