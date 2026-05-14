import importlib.util
from pathlib import Path
from nutev.analysis.prisma import build_prisma_flow
from nutev.export.methods_writer import write_methods_docs
from nutev.export.qualification_writer import write_qualification_outputs


def test_prisma_flow():
    flow=build_prisma_flow([{"url":"a","score":9,"nutev_objects":"evidence_table"},{"url":"a","score":1}], [{"url":"a"}], [{"extraction_status":"ok"}])
    assert flow['registros_identificados']==2


def test_methods_docs(tmp_path: Path):
    write_methods_docs(tmp_path)
    assert (tmp_path / 'NUTEV_METHODS_MASTER.md').exists()


def test_qualification_outputs(tmp_path: Path):
    if importlib.util.find_spec("openpyxl") is None:
        return
    master=[{"workstream":"busca1","title":"t","source":"s","url":"u","file_path":"","year":"2024","score":9,"doc_type":"pdf","domains":"d","main_terms":"adherence","nutev_objects":"questionnaire_item_candidate","translation_potential":"item_questionario","ocr_status":"not_used","extraction_status":"ok","diet_pattern":"dash","clinical_condition":"diabetes","note":"n"}]
    q=[{"workstream":"busca1"}]
    f=[{"componente":"ades"}]
    write_qualification_outputs(master,q,f,tmp_path,tmp_path)
    assert (tmp_path / 'NUTEV_QUALIFICACAO_MASTER.xlsx').exists()
    assert (tmp_path / 'NUTEV_SUMMARY_BUSCA1.md').exists()
