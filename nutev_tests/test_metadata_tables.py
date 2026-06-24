from __future__ import annotations

import csv

from nutev.export.metadata_tables import write_article_data_csv, write_metadata_csv


def _read_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_write_metadata_csv_marks_metadata_only_rows(tmp_path) -> None:
    output = tmp_path / "metadata_master.csv"

    write_metadata_csv(
        [
            {
                "document_id": "doc-1",
                "title": "Metadata only guideline",
                "download_status": "metadata_only",
            }
        ],
        output,
    )

    rows = _read_rows(output)
    assert rows[0]["metadata_status"] == "metadata_only"
    assert rows[0]["download_status"] == "metadata_only"


def test_write_article_data_csv_marks_full_text_rows(tmp_path) -> None:
    output = tmp_path / "article_data.csv"

    write_article_data_csv(
        [
            {
                "document_id": "doc-2",
                "title": "Captured full text",
                "file_path": "05_downloads/doc-2.pdf",
            }
        ],
        output,
    )

    rows = _read_rows(output)
    assert rows[0]["metadata_status"] == "full_text_available"
    assert rows[0]["artifact_paths"] == "05_downloads/doc-2.pdf"


def test_explicit_metadata_status_is_preserved(tmp_path) -> None:
    output = tmp_path / "metadata_master.csv"

    write_metadata_csv(
        [
            {
                "document_id": "doc-3",
                "title": "Preserved status",
                "metadata_status": "capture_failed",
                "download_status": "failed",
            }
        ],
        output,
    )

    rows = _read_rows(output)
    assert rows[0]["metadata_status"] == "capture_failed"
