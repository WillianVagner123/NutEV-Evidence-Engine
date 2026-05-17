import csv

from nutev.export.metadata_tables import write_metadata_csv


def test_metadata_master_has_document_id(tmp_path):
    path = tmp_path / "metadata_master.csv"
    write_metadata_csv([{"document_id": "doc_1", "title": "x", "ocr_status": "used"}], path)
    with path.open() as handle:
        row = next(csv.DictReader(handle))
    assert "document_id" in row
    assert "ocr_status" in row
    assert row["ocr_status"] == "used"
