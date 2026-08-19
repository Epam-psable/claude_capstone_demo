from pathlib import Path

from sync_engine.models import SkipReason, SyncReport, SyncResult
from sync_engine.reporter import Reporter

_SRC = Path("src/sync_engine/module.py")
_DOC = Path("docs/module.md")


def _reporter(repo_root: Path) -> Reporter:
    return Reporter(repo_root)


def test_report_has_four_sections(repo_root, tmp_path):
    report = SyncReport(
        updated=[SyncResult(src_path=_SRC, doc_path=_DOC, status="updated")],
        skipped_no_doc=[SyncResult(src_path=_SRC, doc_path=None, status="skipped", skip_reason=SkipReason.NO_DOC_FILE)],
        skipped_no_section=[SyncResult(src_path=_SRC, doc_path=_DOC, status="skipped", skip_reason=SkipReason.NO_SECTION_MARKER)],
        failed=[],
    )
    out = tmp_path / "report.md"
    content = _reporter(repo_root).generate(report, out)

    assert "## Updated" in content
    assert "## Skipped — No Documentation File" in content
    assert "## Skipped — No Section Marker" in content
    assert "## Failed" in content


def test_report_written_to_file(repo_root, tmp_path):
    report = SyncReport()
    out = tmp_path / "sub" / "report.md"
    _reporter(repo_root).generate(report, out)
    assert out.exists()


def test_summary_line(repo_root, tmp_path):
    report = SyncReport(
        updated=[SyncResult(src_path=_SRC, doc_path=_DOC, status="updated")],
    )
    out = tmp_path / "report.md"
    content = _reporter(repo_root).generate(report, out)
    assert "1 updated" in content
    assert "0 failed" in content


def test_empty_sections_show_none(repo_root, tmp_path):
    report = SyncReport()
    out = tmp_path / "report.md"
    content = _reporter(repo_root).generate(report, out)
    assert content.count("*None*") == 4
