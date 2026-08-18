"""Page object for GitHub Pull Request pages (used in Stage 8 verification)."""
from __future__ import annotations

from playwright.sync_api import Page

from .base_page import BasePage


class GitHubPRPage(BasePage):
    """Represents a GitHub Pull Request detail page."""

    BASE_URL = "https://github.com"

    # Selectors
    _PR_TITLE = "h1.gh-header-title span.js-issue-title"
    _PR_STATE_BADGE = "span.State"
    _PR_BODY = "div.comment-body"
    _FILE_COUNT = "span#files_tab_counter"
    _MERGE_BUTTON = "button.merge-box-button"
    _COMMITS_TAB = "a#commits_tab"
    _PR_LABEL = "a.IssueLabel"

    def __init__(self, page: Page, repo: str) -> None:
        super().__init__(page)
        self._repo = repo  # e.g. "Epam-psable/claude_capstone_demo"

    # --- Navigation ---

    def open_pr(self, pr_number: int) -> None:
        self.navigate(f"{self.BASE_URL}/{self._repo}/pull/{pr_number}")
        self.wait_for_load()

    def open_pr_list(self) -> None:
        self.navigate(f"{self.BASE_URL}/{self._repo}/pulls")
        self.wait_for_load()

    # --- PR metadata ---

    def get_pr_title(self) -> str:
        return self.get_text(self._PR_TITLE).strip()

    def get_pr_state(self) -> str:
        """Returns 'Open', 'Closed', or 'Merged'."""
        return self.get_text(self._PR_STATE_BADGE).strip()

    def get_file_count(self) -> int:
        text = self.get_text(self._FILE_COUNT).strip().replace(",", "")
        return int(text) if text.isdigit() else 0

    def get_pr_body(self) -> str:
        return self.get_text(self._PR_BODY).strip()

    def is_mergeable(self) -> bool:
        return self.page.locator(self._MERGE_BUTTON).is_visible()

    # --- Assertions ---

    def expect_pr_open(self) -> None:
        self.expect_visible(self._PR_STATE_BADGE)
        state = self.get_pr_state()
        assert "Open" in state, f"Expected PR to be Open, got: {state}"

    def expect_pr_title_contains(self, text: str) -> None:
        title = self.get_pr_title()
        assert text in title, f"Expected '{text}' in PR title, got: '{title}'"

    def expect_has_files_changed(self) -> None:
        count = self.get_file_count()
        assert count > 0, "Expected PR to have changed files"
