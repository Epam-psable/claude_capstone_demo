from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Union

from .exceptions import UpdateError
from .models import DocMapping, SkippedFile, SkipReason

logger = logging.getLogger("sync_engine.doc_updater")

# Matches the ## Module Update heading through to the next ## heading or EOF
_SECTION_RE = re.compile(
    r"(## Module Update\s*\n)(.*?)(?=\n## |\Z)",
    re.DOTALL,
)


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
            raise UpdateError(f"Cannot read {self._rel(mapping.doc_path)}: {exc}") from exc

        match = _SECTION_RE.search(original)
        if not match:
            logger.warning(
                "No '## Module Update' section in %s — skipping", self._rel(mapping.doc_path)
            )
            return SkippedFile(path=mapping.src_path, reason=SkipReason.NO_SECTION_MARKER)

        heading = match.group(1)
        updated = _SECTION_RE.sub(heading + new_section_content, original, count=1)

        self._atomic_write(mapping.doc_path, updated)
        logger.info("Updated %s", self._rel(mapping.doc_path))
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
            raise UpdateError(f"Cannot write {self._rel(path)}: {exc}") from exc

    def _rel(self, path: Path) -> str:
        """Return relative path for logging (S-2)."""
        try:
            return str(path.relative_to(self._repo_root))
        except ValueError:
            return str(path)
