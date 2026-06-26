from __future__ import annotations

from nutev.export.metadata_tables import write_simple_csv


def test_write_simple_csv_preserves_headers_for_empty_download_manifest(tmp_path):
    path = tmp_path / "download_manifest.csv"

    write_simple_csv([], path)

    header = path.read_text(encoding="utf-8").splitlines()[0]
    assert header == "document_id,url,resolved_url,path,ext,status,source_provider,workstream"


def test_write_simple_csv_preserves_headers_for_empty_failed_downloads(tmp_path):
    path = tmp_path / "failed_downloads.csv"

    write_simple_csv([], path)

    header = path.read_text(encoding="utf-8").splitlines()[0]
    assert header == "document_id,url,resolved_url,reason,status,source_provider,workstream"


def test_write_simple_csv_keeps_explicit_fieldnames_for_empty_unknown_csv(tmp_path):
    path = tmp_path / "custom_empty.csv"

    write_simple_csv([], path, fieldnames=["a", "b"])

    assert path.read_text(encoding="utf-8").splitlines() == ["a,b"]
