from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

from .models import DocMapping, FileChange, SkippedFile, SkipReason
from .utils import rel_path

logger = logging.getLogger("sync_engine.mapper")


class FileMapper:
    def __init__(self, docs_root: Path, repo_root: Path):
        self._docs_root = docs_root
        self._repo_root = repo_root

    def map(self, change: FileChange) -> Union[DocMapping, SkippedFile]:
        """Map a changed Python file to its Markdown doc by stem (DR-2).

        Returns DocMapping if the doc file exists, SkippedFile(NO_DOC_FILE) otherwise.
        """
        stem = change.path.stem
        doc_path = self._docs_root / f"{stem}.md"

        rel_src = rel_path(change.path, self._repo_root)

        if not doc_path.exists():
            logger.warning("No doc file for %s (expected %s)", rel_src, rel_path(doc_path, self._repo_root))
            return SkippedFile(path=change.path, reason=SkipReason.NO_DOC_FILE)

        logger.debug("Mapped %s -> %s", rel_src, rel_path(doc_path, self._repo_root))
        return DocMapping(src_path=change.path, doc_path=doc_path)
