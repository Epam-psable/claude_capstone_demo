from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Dict, Optional, Set

from .exceptions import AnalysisError
from .models import ChangeSummary

logger = logging.getLogger("sync_engine.analyser")


class AstAnalyser:
    def analyse(
        self,
        src_path: Path,
        old_content: Optional[str],
        new_content: Optional[str],
    ) -> ChangeSummary:
        """Compare old and new source content and return a ChangeSummary.

        old_content=None means the file was added.
        new_content=None means the file was deleted.
        """
        old_defs = self._extract_definitions(src_path, old_content, "old") if old_content is not None else {}
        new_defs = self._extract_definitions(src_path, new_content, "new") if new_content is not None else {}

        old_names: Set[str] = set(old_defs)
        new_names: Set[str] = set(new_defs)

        added = sorted(new_names - old_names)
        removed = sorted(old_names - new_names)
        modified = sorted(
            name for name in old_names & new_names if old_defs[name] != new_defs[name]
        )

        summary = ChangeSummary(src_path=src_path, added=added, removed=removed, modified=modified)
        logger.debug(
            "Analysed %s: +%d added, -%d removed, ~%d modified",
            src_path.name, len(added), len(removed), len(modified),
        )
        return summary

    # --- private ---

    def _extract_definitions(
        self, src_path: Path, content: str, label: str
    ) -> Dict[str, str]:
        """Return {name: source_text} for top-level functions and classes."""
        try:
            tree = ast.parse(content, filename=str(src_path))
        except SyntaxError as exc:
            raise AnalysisError(
                f"Syntax error in {src_path.name} ({label} version) at line {exc.lineno}: {exc.msg}"
            ) from exc

        lines = content.splitlines(keepends=True)
        defs: Dict[str, str] = {}
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start = node.lineno - 1
                end = node.end_lineno  # type: ignore[attr-defined]
                defs[node.name] = "".join(lines[start:end])
        return defs
