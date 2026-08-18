from __future__ import annotations

import logging
import re
from pathlib import Path

from .models import ValidationResult

logger = logging.getLogger("sync_engine.validator")

_SECTION_HEADING_RE = re.compile(r"^## Module Update", re.MULTILINE)


class Validator:
    def validate(self, doc_path: Path, content: str) -> ValidationResult:
        """Validate that updated doc content is structurally complete."""
        errors = []

        if not _SECTION_HEADING_RE.search(content):
            errors.append("## Module Update heading is missing from updated content")

        # Find the section body and check it is non-empty
        match = re.search(
            r"## Module Update\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL
        )
        if match:
            body = match.group(1).strip()
            if not body:
                errors.append("## Module Update section is empty")
        else:
            errors.append("## Module Update section body could not be located")

        result = ValidationResult(is_valid=len(errors) == 0, errors=errors)
        if result.is_valid:
            logger.debug("Validation passed for %s", doc_path.name)
        else:
            logger.error("Validation failed for %s: %s", doc_path.name, "; ".join(errors))
        return result
