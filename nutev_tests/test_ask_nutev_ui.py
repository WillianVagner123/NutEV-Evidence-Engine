from pathlib import Path


WEB = Path("apps/nutev-web")


def read(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def test_evidence_query_uses_safe_rank_blind_context() -> None:
    html = read("ask.html")
    js = read("ask.js")

    assert "Consulta de Evidências" in html
    assert "consulta determinística" in html
    assert "/api/agent-context/article1/status" in js
    assert "ARTICLE_SUMMARIES.jsonl" in js
    assert "full text protegido" in html
    assert "machine_relevance_score" not in js
    assert "reference_rank" not in js
    assert "reference_score" not in js
    assert "reference_tier" not in js
    assert "api.openai.com" not in js
    assert "api.anthropic.com" not in js


def test_evidence_query_is_retrieval_not_scientific_decision() -> None:
    html = read("ask.html")
    js = read("ask.js")

    assert "Consulta ≠ inclusão" in html
    assert "Pertencer a uma rota ≠ elegibilidade" in html
    assert "A Consulta de Evidências não autoriza PRESS, GF-10" in html
    assert "SUPPORTING DOCUMENTS" in js
    assert "Return supporting document IDs" in js
    assert "if(!status.available){showContextUnavailable(status);return}" in js
    guarded_fetch = "fetch(`${baseUrl}ARTICLE_SUMMARIES.jsonl`,{cache:'no-store'})"
    assert guarded_fetch in js
    assert js.index("/api/agent-context/article1/status") < js.index(guarded_fetch)
    assert "não interpreta ausência do pacote como zero evidência" in js
    assert "method:'POST'" not in js.replace(" ", "")
    assert "api.openai.com" not in js
    assert "api.anthropic.com" not in js


def test_evidence_query_packet_points_back_to_scientific_dossier() -> None:
    js = read("ask.js")

    assert "/articles.html?q=" in js
    assert "abra o Dossiê Científico daquele documento" in js
    assert "open the Scientific Dossier for that document" in js
    assert "CONTEXT_MANIFEST.json" in js
    assert "SEARCH_STATE.json" in js
