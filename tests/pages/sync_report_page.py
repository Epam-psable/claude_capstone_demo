"""Page object for the sync report HTML output (docs/sync-report.html)."""
from __future__ import annotations

from playwright.sync_api import Page

from .base_page import BasePage


class SyncReportPage(BasePage):
    """Represents the rendered sync-report page served locally during testing."""

    # Selectors matching the report HTML structure
    _REPORT_TITLE = "h1.report-title"
    _SUMMARY_SECTION = "section#summary"
    _UPDATED_COUNT = "span[data-id='updated-count']"
    _SKIPPED_COUNT = "span[data-id='skipped-count']"
    _FAILED_COUNT = "span[data-id='failed-count']"
    _FILE_ROW = "table#file-results tr.file-row"
    _ERROR_BADGE = "span.badge-error"
    _SUCCESS_BADGE = "span.badge-success"
    _TIMESTAMP = "time[data-id='generated-at']"

    def __init__(self, page: Page, base_url: str = "http://localhost:8080") -> None:
        super().__init__(page)
        self._base_url = base_url

    # --- Navigation ---

    def open(self) -> None:
        self.navigate(f"{self._base_url}/sync-report.html")
        self.wait_for_load()

    # --- Summary data ---

    def get_updated_count(self) -> int:
        text = self.get_text(self._UPDATED_COUNT).strip()
        return int(text) if text.isdigit() else 0

    def get_skipped_count(self) -> int:
        text = self.get_text(self._SKIPPED_COUNT).strip()
        return int(text) if text.isdigit() else 0

    def get_failed_count(self) -> int:
        text = self.get_text(self._FAILED_COUNT).strip()
        return int(text) if text.isdigit() else 0

    def get_file_rows(self) -> list[str]:
        return [
            el.inner_text()
            for el in self.page.locator(self._FILE_ROW).all()
        ]

    def get_timestamp(self) -> str:
        el = self.page.locator(self._TIMESTAMP).first
        return el.get_attribute("datetime") or ""

    def has_errors(self) -> bool:
        return self.page.locator(self._ERROR_BADGE).count() > 0

    # --- Assertions ---

    def expect_no_failures(self) -> None:
        count = self.get_failed_count()
        assert count == 0, f"Expected 0 failures in sync report, got {count}"

    def expect_updated_count(self, expected: int) -> None:
        count = self.get_updated_count()
        assert count == expected, f"Expected {expected} updated files, got {count}"

    def expect_report_title(self, text: str) -> None:
        self.expect_title_contains(text)

    def expect_summary_visible(self) -> None:
        self.expect_visible(self._SUMMARY_SECTION)
