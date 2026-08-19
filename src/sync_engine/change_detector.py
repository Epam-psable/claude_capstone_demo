from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import List, Optional

from .exceptions import SyncError
from .models import FileChange

logger = logging.getLogger("sync_engine.change_detector")


class ChangeDetector:
    def __init__(self, repo_root: Path, source_extensions: List[str]):
        self._repo_root = repo_root
        self._source_extensions = source_extensions

    def detect(self, base_ref: str, head_ref: str) -> List[FileChange]:
        """Return changed source files between base_ref and head_ref."""
        raw = self._git_diff_name_status(base_ref, head_ref)
        changes = []
        for status, path_str in raw:
            path = Path(path_str)
            if path.suffix not in self._source_extensions:
                continue
            old_content = self._git_show(base_ref, path_str) if status != "A" else None  # DR-1
            new_content = self._git_show(head_ref, path_str) if status != "D" else None   # DR-1
            changes.append(FileChange(path=path, status=status, old_content=old_content, new_content=new_content))
            logger.debug("Detected %s: %s", status, path_str)
        logger.info("Detected %d changed source file(s)", len(changes))
        return changes

    def detect_from_list(self, changed_files: List[str]) -> List[FileChange]:
        """Parse explicit 'status:path' entries (manual mode --changed-files).

        old_content is always None — no git ref is available in manual mode, so
        the analyser compares new content against an empty baseline (all items appear as added).
        """
        changes = []
        for entry in changed_files:
            if ":" in entry:
                status, path_str = entry.split(":", 1)
                status = status.strip().upper()
            else:
                status, path_str = "M", entry.strip()
            path = Path(path_str)
            if path.suffix not in self._source_extensions:
                continue
            try:
                new_content = path.read_text(encoding="utf-8") if path.exists() else None
            except OSError as exc:
                logger.warning("Could not read %s: %s", path_str, exc)
                new_content = None
            changes.append(FileChange(path=path, status=status, old_content=None, new_content=new_content))
        logger.info("Parsed %d explicit changed file(s)", len(changes))
        return changes

    # --- private helpers ---

    def _git_diff_name_status(self, base_ref: str, head_ref: str) -> List[tuple]:
        """Run git diff --name-status using shell=False (security constraint S-1)."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-status", base_ref, head_ref],
                capture_output=True,
                text=True,
                check=True,
                shell=False,  # S-1: never shell=True with user-supplied refs
                cwd=self._repo_root,
            )
        except subprocess.CalledProcessError as exc:
            raise SyncError(f"git diff failed: {exc.stderr.strip()}") from exc

        pairs = []
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) == 3:
                # Rename: R{score}\told_path\tnew_path — track the new path (CR-1)
                pairs.append((parts[0][0].upper(), parts[2].strip()))
            elif len(parts) == 2:
                pairs.append((parts[0][0].upper(), parts[1].strip()))
        return pairs

    def _git_show(self, ref: str, path: str) -> Optional[str]:
        """Fetch file content at a git ref using shell=False (S-1, DR-1)."""
        try:
            result = subprocess.run(
                ["git", "show", f"{ref}:{path}"],
                capture_output=True,
                text=True,
                check=True,
                shell=False,  # S-1
                cwd=self._repo_root,
            )
            return result.stdout
        except subprocess.CalledProcessError:
            logger.debug("Could not fetch %s at ref %s (may be new file)", path, ref)
            return None
