from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Union

from .exceptions import UpdateError
from .models import DocMapping, SkippedFile, SkipReason
from .utils import SECTION_RE, rel_path

logger = logging.getLogger("sync_engine.doc_updater")


class DocUpdater:
    def __init__(self, repo_root: Path):
        self._repo_root = repo_root

    def update(self, mapping: DocMapping, new_section_content: str) -> Union[None, SkippedFile]:
        """Replace ## Module Update section in the doc file.

        Returns SkippedFile(NO_SECTION_MARKER) if the section is absent.
        Raises UpdateError if the write fails.
        Uses atomic write: write to .tmp then os.replace() (MC-1).
        """
        try:
            original = mapping.doc_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise UpdateError(f"Cannot read {rel_path(mapping.doc_path, self._repo_root)}: {exc}") from exc

        match = SECTION_RE.search(original)
        if not match:
            logger.warning(
                "No '## Module Update' section in %s — skipping",
                rel_path(mapping.doc_path, self._repo_root),
            )
            return SkippedFile(path=mapping.src_path, reason=SkipReason.NO_SECTION_MARKER)

        heading = match.group(1)
        updated = SECTION_RE.sub(heading + new_section_content, original, count=1)

        self._atomic_write(mapping.doc_path, updated)
        logger.info("Updated %s", rel_path(mapping.doc_path, self._repo_root))
        return None

    # --- private ---

    def _atomic_write(self, path: Path, content: str) -> None:
        """Write content atomically: write to .tmp then os.replace() (MC-1)."""
        tmp_path = path.with_suffix(".md.tmp")
        try:
            tmp_path.write_text(content, encoding="utf-8")
            os.replace(tmp_path, path)
        except OSError as exc:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise UpdateError(f"Cannot write {rel_path(path, self._repo_root)}: {exc}") from exc
