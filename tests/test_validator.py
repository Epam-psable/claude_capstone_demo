from pathlib import Path

from sync_engine.validator import Validator

_PATH = Path("docs/module.md")


def test_valid_content():
    content = "# Module\n\n## Module Update\n\n*Last synced: today*\n\n### Added\n- `f`\n"
    result = Validator().validate(_PATH, content)
    assert result.is_valid
    assert not result.errors


def test_missing_heading():
    content = "# Module\n\nNo section here.\n"
    result = Validator().validate(_PATH, content)
    assert not result.is_valid
    assert any("heading" in e.lower() for e in result.errors)


def test_empty_section_body():
    content = "# Module\n\n## Module Update\n\n\n"
    result = Validator().validate(_PATH, content)
    assert not result.is_valid
    assert any("empty" in e.lower() for e in result.errors)


def test_section_with_only_whitespace():
    content = "# Module\n\n## Module Update\n\n   \n\n"
    result = Validator().validate(_PATH, content)
    assert not result.is_valid
