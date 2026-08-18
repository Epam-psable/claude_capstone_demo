from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import yaml
from dotenv import load_dotenv

from .exceptions import ConfigurationError

logger = logging.getLogger("sync_engine.config_manager")


@dataclass
class Config:
    docs_root: Path
    source_extensions: List[str]
    docs_glob: str = "*.md"
    readme_filename: str = "README.md"
    log_level: str = "INFO"
    sync_report_output: Path = Path("artifacts/sync-report.md")


class ConfigManager:
    def __init__(self, config_path: Path, env_path: Optional[Path] = None):
        self._config_path = config_path
        self._env_path = env_path

    def load(self) -> Config:
        """Load and validate config. Raises ConfigurationError before pipeline starts (M-1)."""
        if self._env_path and self._env_path.exists():
            load_dotenv(self._env_path)

        if not self._config_path.exists():
            raise ConfigurationError(f"Config file not found: {self._config_path}")

        try:
            with open(self._config_path, encoding="utf-8") as fh:
                raw = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise ConfigurationError(f"Config file is invalid YAML: {exc}") from exc

        if not raw:
            raise ConfigurationError("Config file is empty")

        missing = [f for f in ("docs_root", "source_extensions") if f not in raw]
        if missing:
            raise ConfigurationError(f"Config missing required field(s): {', '.join(missing)}")

        docs_root = Path(os.getenv("DOCS_ROOT", raw["docs_root"]))
        sync_report = Path(os.getenv("SYNC_REPORT_OUTPUT", "artifacts/sync-report.md"))

        logger.debug("Config loaded: docs_root=%s extensions=%s", docs_root, raw["source_extensions"])
        return Config(
            docs_root=docs_root,
            source_extensions=raw["source_extensions"],
            docs_glob=raw.get("docs_glob", "*.md"),
            readme_filename=raw.get("readme_filename", "README.md"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            sync_report_output=sync_report,
        )
