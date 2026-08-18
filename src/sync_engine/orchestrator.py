from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional

from .analyser import AstAnalyser
from .change_detector import ChangeDetector
from .config_manager import ConfigManager
from .doc_updater import DocUpdater
from .exceptions import AnalysisError, SyncError, UpdateError, ValidationError
from .mapper import FileMapper
from .models import DocMapping, SkipReason, SkippedFile, SyncReport, SyncResult
from .reporter import Reporter
from .update_generator import UpdateGenerator
from .validator import Validator

logger = logging.getLogger("sync_engine.orchestrator")


class Orchestrator:
    def __init__(self, repo_root: Path, config_path: Path, env_path: Optional[Path] = None):
        self._repo_root = repo_root
        self._config_path = config_path
        self._env_path = env_path

    def run(
        self,
        base_ref: Optional[str] = None,
        head_ref: Optional[str] = None,
        changed_files: Optional[List[str]] = None,
    ) -> int:
        """Run the full pipeline. Returns 0 on success, 1 if any matched file failed (EH-2)."""
        # Phase 1: load and validate config before anything else (M-1)
        config = ConfigManager(self._config_path, self._env_path).load()

        _configure_logging(config.log_level)

        # Resolve relative config paths against repo_root
        docs_root = (
            config.docs_root if config.docs_root.is_absolute()
            else self._repo_root / config.docs_root
        )
        report_output = (
            config.sync_report_output if config.sync_report_output.is_absolute()
            else self._repo_root / config.sync_report_output
        )

        detector = ChangeDetector(self._repo_root, config.source_extensions)
        mapper = FileMapper(docs_root, self._repo_root)
        analyser = AstAnalyser()
        generator = UpdateGenerator()
        updater = DocUpdater(self._repo_root)
        validator = Validator()
        reporter = Reporter(self._repo_root)

        # Phase 2: detect changes
        if changed_files:
            file_changes = detector.detect_from_list(changed_files)
        elif base_ref and head_ref:
            file_changes = detector.detect(base_ref, head_ref)
        else:
            logger.error("No change source specified (provide refs or --changed-files)")
            return 1

        if not file_changes:
            logger.info("Nothing to sync — no Python source changes detected")
            try:
                reporter.generate(SyncReport(), report_output)
            except UpdateError as exc:
                logger.error("Failed to write sync report: %s", exc)
            return 0

        # Phase 3–6: process each changed file
        sync_report = SyncReport()

        for change in file_changes:
            mapping = mapper.map(change)

            if isinstance(mapping, SkippedFile):
                result = SyncResult(
                    src_path=change.path,
                    doc_path=None,
                    status="skipped",
                    skip_reason=mapping.reason,
                )
                if mapping.reason == SkipReason.NO_DOC_FILE:
                    sync_report.skipped_no_doc.append(result)
                else:
                    sync_report.skipped_no_section.append(result)
                continue

            # mapping is a DocMapping — process it
            try:
                summary = analyser.analyse(change.path, change.old_content, change.new_content)
                section_content = generator.generate(summary)

                # Compose in memory first (CR-1: validate before write — FR-8, AC4)
                composed = updater.compose(mapping, section_content)
                if isinstance(composed, SkippedFile):
                    sync_report.skipped_no_section.append(
                        SyncResult(
                            src_path=change.path,
                            doc_path=mapping.doc_path,
                            status="skipped",
                            skip_reason=SkipReason.NO_SECTION_MARKER,
                        )
                    )
                    continue

                # Validate before writing — blocks save on failure (FR-8, AC4)
                val_result = validator.validate(mapping.doc_path, composed)
                if not val_result.is_valid:
                    raise ValidationError("; ".join(val_result.errors))

                # Write only after validation passes
                updater.write(mapping, composed)

                sync_report.updated.append(
                    SyncResult(
                        src_path=change.path,
                        doc_path=mapping.doc_path,
                        status="updated",
                    )
                )

            except (AnalysisError, UpdateError, ValidationError, SyncError) as exc:
                logger.error("Failed to process %s: %s", change.path.name, exc)
                sync_report.failed.append(
                    SyncResult(
                        src_path=change.path,
                        doc_path=mapping.doc_path if isinstance(mapping, DocMapping) else None,
                        status="failed",
                        error_message=str(exc),
                    )
                )

        try:
            reporter.generate(sync_report, report_output)
        except UpdateError as exc:
            logger.error("Failed to write sync report: %s", exc)

        # EH-2: exit 1 only if matched files failed; skips do not count
        return 1 if sync_report.has_failures else 0


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
