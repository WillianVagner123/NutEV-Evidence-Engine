from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def _text(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def test_article_dossier_hides_internal_model_branding():
    text = _text("articles.js")
    for visible_legacy in (
        "contexto IA",
        "chamadas externas de LLM",
        "texto integral enviado para LLM",
        "Subtipo documental preservado do Workbench",
        "Workbench ainda sem índice",
        "Workbench indisponível",
        "Nenhum ResultBundle materializado",
        "score operacional",
        "rank #",
    ):
        assert visible_legacy not in text

    for system_term in (
        "contexto estruturado",
        "Biblioteca de evidências",
        "pacote de resultados",
        "pontuação operacional",
        "Proveniência e processamento",
        "Texto processado ou extraído pelo sistema",
    ):
        assert system_term in text

    # Internal compatibility fields may remain in code; they are not product labels.
    assert "llm_context_chars" in text


def test_article_dossier_dynamic_copy_is_bilingual():
    text = _text("articles.js")
    assert "import './i18n.js'" in text
    assert "window.NutEVI18n?.language==='en'" in text
    assert "window.addEventListener('nutev:language-change',resetAndLoad)" in text
    for english_term in (
        "Evidence library unavailable",
        "operational score",
        "structured context",
        "Provenance and processing",
        "Verbatim source excerpt",
    ):
        assert english_term in text


def test_interpretation_workflow_uses_system_terms_not_legacy_labels():
    text = _text("evidence-interpretation.js")
    for visible_legacy in (
        "Scientific Intelligence",
        "finding-ready",
        "result bundles para inspeção",
        "síntese estrutural rank-blind",
        "Nenhum round explícito",
        "desta ResearchApplication",
    ):
        assert visible_legacy not in text

    for system_term in (
        "Mapa de Evidências",
        "Análise de Evidências",
        "Controle de Revisão",
        "pronto para inspeção",
        "pacote de resultados",
        "Progresso de envio humano",
        "Aplicação de pesquisa",
    ):
        assert system_term in text


def test_interpretation_workflow_rerenders_on_language_change():
    text = _text("evidence-interpretation.js")
    assert "import './i18n.js'" in text
    assert "window.NutEVI18n?.t" in text
    assert "window.addEventListener('nutev:language-change'" in text
    assert "Evidence Analysis" in text
    assert "ready for inspection" in text
    assert "Human submission progress" in text


def test_global_glossary_is_system_first_and_bilingual():
    text = _text("product-ui.js")
    assert "['Sistema de Evidências Científicas'" in text
    assert "['Fonte'" in text
    assert "['Ordenação de busca'" in text
    assert "['Espaço de trabalho'" in text
    assert "['Consulta de Evidências'" in text
    assert "['Contexto de Evidências'" in text
    assert "['Pacote de Evidências'" in text
    assert "['Bloqueio por segurança'" in text
    assert "['Provider'" not in text
    assert "['Ranking'" not in text
    assert "['Workspace'" not in text

    assert "Scientific Evidence System" in text
    assert "Evidence Query" in text
    assert "Evidence Context" in text
    assert "Fail-closed safeguard" in text
    assert "refreshGlossary" in text
    assert "nutev:language-change" in text
