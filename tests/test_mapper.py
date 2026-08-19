from pathlib import Path

from sync_engine.mapper import FileMapper
from sync_engine.models import DocMapping, FileChange, SkippedFile, SkipReason


def _make_change(path: Path) -> FileChange:
    return FileChange(path=path, status="M", old_content="", new_content="")


def test_map_found(repo_root, docs_dir, src_dir):
    doc = docs_dir / "mapper.md"
    doc.write_text("# Mapper\n\n## Module Update\n\nOld\n", encoding="utf-8")
    src = src_dir / "mapper.py"

    mapper = FileMapper(docs_dir, repo_root)
    result = mapper.map(_make_change(src))

    assert isinstance(result, DocMapping)
    assert result.doc_path == doc
    assert result.src_path == src


def test_map_no_doc_file(repo_root, docs_dir, src_dir):
    src = src_dir / "unknown.py"
    mapper = FileMapper(docs_dir, repo_root)
    result = mapper.map(_make_change(src))

    assert isinstance(result, SkippedFile)
    assert result.reason == SkipReason.NO_DOC_FILE
    assert result.path == src


def test_map_uses_stem(repo_root, docs_dir, src_dir):
    doc = docs_dir / "utils.md"
    doc.write_text("", encoding="utf-8")
    src = src_dir / "utils.py"

    mapper = FileMapper(docs_dir, repo_root)
    result = mapper.map(_make_change(src))

    assert isinstance(result, DocMapping)
    assert result.doc_path.name == "utils.md"
