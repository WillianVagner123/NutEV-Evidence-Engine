from __future__ import annotations

from nutev.export.metadata_tables import write_simple_csv


def test_write_simple_csv_preserves_explicit_header_for_empty_rows(tmp_path) -> None:
    path = tmp_path / "empty.csv"

    write_simple_csv([], path, fieldnames=["document_id", "title"])

    assert path.read_text(encoding="utf-8").splitlines() == ["document_id,title"]


def test_write_simple_csv_ignores_extra_fields_when_schema_is_explicit(tmp_path) -> None:
    path = tmp_path / "rows.csv"

    write_simple_csv(
        [{"document_id": "doc_1", "title": "A", "extra": "ignored"}],
        path,
        fieldnames=["document_id", "title"],
    )

    assert path.read_text(encoding="utf-8").splitlines() == [
        "document_id,title",
        "doc_1,A",
    ]
