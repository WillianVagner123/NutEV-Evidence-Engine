import csv

from nutev.export.metadata_tables import write_metadata_csv


def test_metadata_master_has_document_id(tmp_path):
    path = tmp_path / "metadata_master.csv"
    write_metadata_csv([{"document_id": "doc_1", "title": "x"}], path)
    with path.open() as f:
        row = next(csv.DictReader(f))
    assert "document_id" in row
