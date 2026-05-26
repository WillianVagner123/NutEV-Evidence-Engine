from pathlib import Path
from unittest.mock import Mock
import importlib.util

from nutev.analysis.synthesis import build_master_rows, classify_nutev_objects, build_questionnaire_candidates, build_framework_components, write_synthesis_outputs
from nutev.download.downloader import _request_with_retry as _get_with_retry_response
from nutev.extract.smart_extract import extract_document


def test_classify_objects_and_candidates(tmp_path: Path):
    rows=[{"workstream":"busca1","title":"Guideline adherence framework","source":"pubmed","url":"u","relevance_score":9,"extracted_text":"behavior adherence implementation"}]
    master=build_master_rows(rows)
    objs=classify_nutev_objects(rows[0])
    assert "recommendation_map" in objs
    q=build_questionnaire_candidates(master)
    assert len(q)>=1
    f=build_framework_components(master)
    assert len(f)>=1


def test_synthesis_export(tmp_path: Path):
    if importlib.util.find_spec("openpyxl") is None:
        return
    master=[{"workstream":"busca1","title":"t","source":"s","url":"u","file_path":"","year":"2024","score":1,"doc_type":"pdf","domains":"d","main_terms":"m","nutev_objects":"domain_map","translation_potential":"mapa_dominio","ocr_status":"not_used","extraction_status":"ok","diet_pattern":"","clinical_condition":"","note":"n"}]
    write_synthesis_outputs(master, tmp_path)
    assert (tmp_path / "NUTEV_EVIDENCE_MASTER.xlsx").exists()


def test_retry_logic():
    s=Mock()
    resp=Mock(); resp.raise_for_status.return_value=None; resp.status_code=200; resp.content=b"abc"
    s.get.side_effect=[Exception("x"), resp]
    out=_get_with_retry_response(s, "http://x", Mock(), retries=2)
    assert out.content == b"abc"


def test_ocr_fallback_smoke(tmp_path: Path):
    p=tmp_path/"a.pdf"; p.write_bytes(b"%PDF-1.4 fake")
    res=extract_document(p, tmp_path/"ocr", tmp_path/"ext", Mock())
    assert "extraction_status" in res
