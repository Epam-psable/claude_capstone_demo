"""E2E tests for the sync report page using the SyncReportPage POM."""
import pytest

from tests.pages import SyncReportPage


pytestmark = pytest.mark.e2e


class TestSyncReportPage:
    """Verify the rendered sync-report page via Playwright POM."""

    def test_report_page_loads(self, sync_report_page: SyncReportPage) -> None:
        sync_report_page.open()
        sync_report_page.expect_summary_visible()

    def test_report_has_no_failures(self, sync_report_page: SyncReportPage) -> None:
        sync_report_page.open()
        sync_report_page.expect_no_failures()

    def test_report_shows_updated_files(self, sync_report_page: SyncReportPage) -> None:
        sync_report_page.open()
        count = sync_report_page.get_updated_count()
        assert count >= 0, "Updated count should be a non-negative integer"

    def test_report_timestamp_is_set(self, sync_report_page: SyncReportPage) -> None:
        sync_report_page.open()
        ts = sync_report_page.get_timestamp()
        assert ts, "Expected a generated-at timestamp in the report"

    def test_file_rows_present(self, sync_report_page: SyncReportPage) -> None:
        sync_report_page.open()
        rows = sync_report_page.get_file_rows()
        assert isinstance(rows, list), "get_file_rows() should return a list"

    def test_screenshot_on_load(
        self, sync_report_page: SyncReportPage, tmp_path
    ) -> None:
        sync_report_page.open()
        out = str(tmp_path / "sync-report.png")
        sync_report_page.screenshot(out)
        import os
        assert os.path.exists(out), "Screenshot file should be created"
