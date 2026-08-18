from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from .exceptions import UpdateError
from .models import SyncReport, SyncResult
from .utils import rel_path

logger = logging.getLogger("sync_engine.reporter")


class Reporter:
    def __init__(self, repo_root: Path):
        self._repo_root = repo_root

    def generate(self, report: SyncReport, output_path: Path) -> str:
        """Render SyncReport to Markdown, print to stdout, write to output_path."""
        content = self._render(report)
        print(content)
        self._write(output_path, content)
        logger.info("Sync report written to %s", rel_path(output_path, self._repo_root))
        return content

    # --- private ---

    def _render(self, report: SyncReport) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            "# Sync Report",
            "",
            f"Generated: {timestamp}",
            "",
        ]

        # Updated
        lines.append(f"## Updated ({len(report.updated)})")
        lines.append("")
        if report.updated:
            lines.append("| Source File | Documentation File |")
            lines.append("|-------------|-------------------|")
            for r in report.updated:
                lines.append(f"| `{self._rp(r.src_path)}` | `{self._rp(r.doc_path)}` |")
        else:
            lines.append("*None*")
        lines.append("")

        # Skipped — no doc file (EH-1: separate from no-section)
        lines.append(f"## Skipped — No Documentation File ({len(report.skipped_no_doc)})")
        lines.append("")
        if report.skipped_no_doc:
            lines.append("| Source File | Reason |")
            lines.append("|-------------|--------|")
            for r in report.skipped_no_doc:
                lines.append(f"| `{self._rp(r.src_path)}` | No matching `.md` file in docs/ |")
        else:
            lines.append("*None*")
        lines.append("")

        # Skipped — no section marker (EH-1)
        lines.append(f"## Skipped — No Section Marker ({len(report.skipped_no_section)})")
        lines.append("")
        if report.skipped_no_section:
            lines.append("| Source File | Documentation File | Reason |")
            lines.append("|-------------|-------------------|--------|")
            for r in report.skipped_no_section:
                lines.append(
                    f"| `{self._rp(r.src_path)}` | `{self._rp(r.doc_path)}` | No `## Module Update` section |"
                )
        else:
            lines.append("*None*")
        lines.append("")

        # Failed
        lines.append(f"## Failed ({len(report.failed)})")
        lines.append("")
        if report.failed:
            lines.append("| Source File | Error |")
            lines.append("|-------------|-------|")
            for r in report.failed:
                lines.append(f"| `{self._rp(r.src_path)}` | {r.error_message or 'Unknown error'} |")
        else:
            lines.append("*None*")
        lines.append("")

        lines.append("---")
        n_skip = len(report.skipped_no_doc) + len(report.skipped_no_section)
        lines.append(
            f"**Summary:** {len(report.updated)} updated, "
            f"{n_skip} skipped, "
            f"{len(report.failed)} failed "
            f"(total processed: {report.total_processed})"
        )
        lines.append("")

        return "\n".join(lines)

    def _write(self, output_path: Path, content: str) -> None:
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
        except OSError as exc:
            raise UpdateError(f"Cannot write report to {rel_path(output_path, self._repo_root)}: {exc}") from exc

    def _rp(self, path: Path) -> str:
        """Relative path for report display (S-2: no absolute paths in output)."""
        if path is None:
            return ""
        return rel_path(path, self._repo_root)
