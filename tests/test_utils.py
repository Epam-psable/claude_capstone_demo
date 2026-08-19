"""Unit tests for sync_engine.utils — shared rel_path and SECTION_RE."""
import pytest
from pathlib import Path

from sync_engine.utils import SECTION_RE, rel_path


class TestRelPath:
    def test_returns_relative_for_path_inside_repo(self, tmp_path):
        target = tmp_path / "src" / "foo.py"
        result = rel_path(target, tmp_path)
        assert result == str(Path("src/foo.py"))

    def test_returns_str_for_path_outside_repo(self, tmp_path):
        outside = tmp_path.parent / "other" / "file.py"
        result = rel_path(outside, tmp_path)
        assert result == str(outside)

    def test_repo_root_itself_returns_dot(self, tmp_path):
        result = rel_path(tmp_path, tmp_path)
        assert result == "."

    def test_nested_path(self, tmp_path):
        target = tmp_path / "a" / "b" / "c.py"
        result = rel_path(target, tmp_path)
        assert result == str(Path("a/b/c.py"))


class TestSectionRE:
    def test_matches_section_followed_by_next_heading(self):
        doc = "# Title\n\n## Module Update\n\nBody text.\n\n## Other\n\nKept.\n"
        match = SECTION_RE.search(doc)
        assert match is not None
        assert "Body text" in match.group(2)
        assert "Kept" not in match.group(2)

    def test_matches_section_at_eof(self):
        doc = "# Title\n\n## Module Update\n\nContent at end"
        match = SECTION_RE.search(doc)
        assert match is not None
        assert "Content at end" in match.group(2)

    def test_no_match_without_section(self):
        doc = "# Title\n\nNo update section here.\n"
        assert SECTION_RE.search(doc) is None

    def test_group_1_is_heading_line(self):
        doc = "## Module Update\n\nbody\n"
        match = SECTION_RE.search(doc)
        assert match.group(1).startswith("## Module Update")

    def test_group_2_is_body(self):
        doc = "## Module Update\n\nbody text\n"
        match = SECTION_RE.search(doc)
        assert "body text" in match.group(2)

    def test_substitution_replaces_only_body(self):
        doc = "Before\n\n## Module Update\n\nOld body.\n\n## Next\n\nAfter.\n"
        result = SECTION_RE.sub(r"\g<1>New body.\n", doc, count=1)
        assert "New body" in result
        assert "Old body" not in result
        assert "Before" in result
        assert "After" in result
