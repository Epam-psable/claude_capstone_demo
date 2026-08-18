from __future__ import annotations

import logging
from datetime import date

from .models import ChangeSummary

logger = logging.getLogger("sync_engine.update_generator")


class UpdateGenerator:
    def generate(self, summary: ChangeSummary) -> str:
        """Format a ChangeSummary into the Markdown content for ## Module Update."""
        lines = [f"*Last synced: {date.today().isoformat()}*", ""]

        if not summary.has_changes:
            lines.append("*No API-level changes detected in this update.*")
            return "\n".join(lines)

        if summary.added:
            lines.append("### Added")
            for name in summary.added:
                lines.append(f"- `{name}`")
            lines.append("")

        if summary.removed:
            lines.append("### Removed")
            for name in summary.removed:
                lines.append(f"- `{name}`")
            lines.append("")

        if summary.modified:
            lines.append("### Modified")
            for name in summary.modified:
                lines.append(f"- `{name}`")
            lines.append("")

        content = "\n".join(lines).rstrip() + "\n"
        logger.debug(
            "Generated update for %s: %d added, %d removed, %d modified",
            summary.src_path.name, len(summary.added), len(summary.removed), len(summary.modified),
        )
        return content
