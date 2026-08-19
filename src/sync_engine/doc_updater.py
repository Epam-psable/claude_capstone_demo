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

    def compose(self, mapping: DocMapping, new_section_content: str) -> Union[str, SkippedFile]:
        """Build updated doc content in memory without writing to disk.

        Returns the composed string, or SkippedFile(NO_SECTION_MARKER) if absent.
        Raises UpdateError if the file cannot be read.
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
        return SECTION_RE.sub(heading + new_section_content, original, count=1)

    def write(self, mapping: DocMapping, content: str) -> None:
        """Write composed content to disk atomically (MC-1)."""
        self._atomic_write(mapping.doc_path, content)
        logger.info("Updated %s", rel_path(mapping.doc_path, self._repo_root))

    def update(self, mapping: DocMapping, new_section_content: str) -> Union[None, SkippedFile]:
        """Compose and write in one step. Returns SkippedFile if section is absent."""
        result = self.compose(mapping, new_section_content)
        if isinstance(result, SkippedFile):
            return result
        self.write(mapping, result)
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
