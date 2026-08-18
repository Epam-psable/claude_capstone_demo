from __future__ import annotations

import re
from pathlib import Path

# Shared section regex — matches ## Module Update heading through to next ## heading or EOF.
# Used by both DocUpdater (write) and Validator (read).
SECTION_RE = re.compile(
    r"(## Module Update\s*\n)(.*?)(?=\n## |\Z)",
    re.DOTALL,
)


def rel_path(path: Path, repo_root: Path) -> str:
    """Return path relative to repo_root for display; fall back to str(path)."""
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)
