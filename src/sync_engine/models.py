from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional


class SkipReason(Enum):
    NO_DOC_FILE = "no_doc_file"
    NO_SECTION_MARKER = "no_section_marker"


@dataclass
class FileChange:
    path: Path
    status: str  # A=added, M=modified, D=deleted, R=renamed
    old_content: Optional[str]  # None for added files (DR-1)
    new_content: Optional[str]  # None for deleted files (DR-1)


@dataclass
class DocMapping:
    src_path: Path
    doc_path: Path


@dataclass
class SkippedFile:
    path: Path
    reason: SkipReason  # DR-2


@dataclass
class ChangeSummary:
    src_path: Path
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.modified)


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)


@dataclass
class SyncResult:
    src_path: Path
    doc_path: Optional[Path]
    status: str  # "updated" | "skipped" | "failed"
    skip_reason: Optional[SkipReason] = None
    error_message: Optional[str] = None


@dataclass
class SyncReport:
    updated: List[SyncResult] = field(default_factory=list)
    skipped_no_doc: List[SyncResult] = field(default_factory=list)
    skipped_no_section: List[SyncResult] = field(default_factory=list)
    failed: List[SyncResult] = field(default_factory=list)

    @property
    def total_processed(self) -> int:
        return (
            len(self.updated)
            + len(self.skipped_no_doc)
            + len(self.skipped_no_section)
            + len(self.failed)
        )

    @property
    def has_failures(self) -> bool:
        return bool(self.failed)
