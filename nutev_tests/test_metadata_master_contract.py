import csv

from nutev.export.metadata_tables import write_metadata_csv, write_simple_csv


def test_metadata_master_has_document_id(tmp_path):
    path = tmp_path / "metadata_master.csv"
    write_metadata_csv([{"document_id": "doc_1", "title": "x"}], path)
    with path.open() as f:
        row = next(csv.DictReader(f))
    assert "document_id" in row


def test_write_simple_csv_preserves_known_empty_contract(tmp_path):
    path = tmp_path / "download_manifest.csv"
    write_simple_csv([], path)

    with path.open(encoding="utf-8") as f:
        header = next(csv.reader(f))

    assert header == ["url", "resolved_url", "path", "ext", "source", "status"]


def test_write_simple_csv_uses_explicit_fieldnames_for_empty_rows(tmp_path):
    path = tmp_path / "custom.csv"
    write_simple_csv([], path, fieldnames=["a", "b"])

    with path.open(encoding="utf-8") as f:
        header = next(csv.reader(f))

    assert header == ["a", "b"]
