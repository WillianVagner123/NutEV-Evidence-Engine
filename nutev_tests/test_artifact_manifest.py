import csv

from nutev.engine.artifacts import build_artifact_manifest


def test_artifact_manifest_records_sha256(tmp_path):
    f = tmp_path / "a.txt"
    f.write_text("abc", encoding="utf-8")
    out = tmp_path / "artifact_manifest.csv"
    build_artifact_manifest([{"document_id": "doc_1", "artifact_type": "txt", "path": str(f), "source_stage": "test"}], out)
    with out.open() as handle:
        row = next(csv.DictReader(handle))
    assert row["sha256"]
