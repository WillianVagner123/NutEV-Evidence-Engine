"""Contracts for the deterministic question planner (question -> blocks -> per-source strings).

Python (src/nutev/search/question_planner.py) is canonical; the browser port
(apps/nutev-open/planner.js) must produce identical plans and strings.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from nutev.search.question_planner import (
    QueryVocabularyError,
    compile_queries,
    encode_component,
    load_query_vocabulary,
    plan_question,
    to_review_strategy,
    validate_query_vocabulary,
)
from nutev.taxonomy import load_canonical_taxonomy

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
HARNESS = ROOT / "nutev_tests" / "fixtures" / "open_explorer_harness.cjs"
YEAR = 2026

VOCABULARY = load_query_vocabulary(CONFIG)
TAXONOMY, _TAXONOMY_META = load_canonical_taxonomy(CONFIG)

QUESTIONS = [
    "A dieta mediterrânea melhora o controle glicêmico em adultos com diabetes tipo 2?",
    "efeito do kefir na microbiota intestinal de idosos nos últimos 10 anos",
    "plant-based diet vs mediterranean diet for weight loss in obese adults: systematic review",
    "letramento alimentar e oficinas culinárias na atenção primária no Brasil desde 2015",
    "ultraprocessados e obesidade em crianças e adolescentes entre 2010 e 2020",
    "Medicina do Estilo de Vida na hipertensão: ensaios clínicos randomizados",
    "jejum intermitente comparado com restrição calórica para perda de peso",
    "sono, estresse e mindfulness em trabalhadores com síndrome metabólica",
    "food insecurity produce prescription programs diabetes outcomes 2015-2023",
    "Qual o impacto do consumo de bebidas açucaradas na pressão arterial de gestantes antes de 2010?",
    "fermented foods and depressive symptoms",
    "dieta DASH, sódio e hipertensão em idosos brasileiros",
    "health coaching and motivational interviewing for weight loss in primary care: meta-analysis",
    "comensalidade e refeições em família em escolares nos últimos cinco anos",
    "DPP implementation in community settings since 2018",
    "Ômega-3 e marcadores inflamatórios na doença renal crônica",
    "telessaúde para autocuidado em diabetes",
    "a b c de e",
    "",
    '("mediterranean diet"[tiab]) AND diabetes',
    "diabetes OR obesity",
    "TITLE_ABS:\"lifestyle medicine\"",
    "nutrição do estilo de vida e qualidade da dieta em mulheres",
    "vegan vs vegetarian diets cholesterol LDL",
    "Pré-diabetes, sobrepeso e atividade física: coorte prospectiva entre 2000 e 2010",
]

OPTIONS = [
    {"fieldMode": "title_abstract", "includePt": False},
    {"fieldMode": "broad", "includePt": False},
    {"fieldMode": "title_abstract", "includePt": True},
]


def _plan(question: str, **kwargs: Any) -> dict[str, Any]:
    return plan_question(question, VOCABULARY, taxonomy_groups=TAXONOMY, current_year=YEAR, **kwargs)


def _run_harness(payload: dict[str, Any]) -> dict[str, Any]:
    result = subprocess.run(
        ["node", "--unhandled-rejections=strict", str(HARNESS)],
        cwd=ROOT,
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def _concepts(plan: dict[str, Any]) -> dict[str, tuple[str, bool]]:
    return {
        concept: (block["role"], block["enabled"])
        for block in plan["blocks"]
        for concept in block["concept_ids"]
    }


# ----------------------------------------------------------------------- vocabulary


def test_vocabulary_is_valid_and_linked_to_canonical_taxonomy():
    validate_query_vocabulary(VOCABULARY, set(TAXONOMY))
    groups = {c["taxonomy_group"] for c in VOCABULARY["concepts"] if c.get("taxonomy_group")}
    assert groups <= set(TAXONOMY)
    assert VOCABULARY["review_status"] == "curated_pending_human_review"
    assert len(VOCABULARY["concepts"]) >= 90


def test_vocabulary_never_ships_controlled_headings_as_search_terms():
    for concept in VOCABULARY["concepts"]:
        for term in [*concept["en"], *concept.get("pt", [])]:
            assert "[" not in term and ":" not in term, (concept["id"], term)
        for item in concept.get("pubmed_filters", []):
            assert concept["role"] == "design", concept["id"]
            assert item.endswith("[pt]") or item.endswith("[sb]"), item


def test_ambiguous_triggers_fail_closed():
    broken = json.loads(json.dumps(VOCABULARY))
    broken["concepts"][1]["triggers"].append(broken["concepts"][0]["triggers"][0])
    with pytest.raises(QueryVocabularyError, match="ambiguous"):
        validate_query_vocabulary(broken)


def test_unknown_taxonomy_group_fails_closed():
    broken = json.loads(json.dumps(VOCABULARY))
    broken["concepts"][0]["taxonomy_group"] = "domain.does_not_exist"
    with pytest.raises(QueryVocabularyError, match="taxonomy_group"):
        validate_query_vocabulary(broken, set(TAXONOMY))


# ----------------------------------------------------------------------- understanding


def test_portuguese_question_becomes_english_pico_blocks():
    plan = _plan(QUESTIONS[0])
    concepts = _concepts(plan)
    assert concepts["condition.type2_diabetes"] == ("population", True)
    assert concepts["diet.mediterranean"] == ("intervention", True)
    assert concepts["outcome.glycemic_control"] == ("outcome", True)
    assert concepts["population.adults"] == ("population", False)
    pubmed = compile_queries(plan, current_year=YEAR)["providers"]["pubmed"]["query"]
    assert '"mediterranean diet"[tiab]' in pubmed
    assert '"type 2 diabetes"[tiab]' in pubmed
    assert "HbA1c" in pubmed
    assert "dieta mediterr" not in pubmed and "melhora" not in pubmed
    assert plan["dropped_terms"] == ["a", "melhora", "o", "em", "com"]


def test_unknown_words_are_kept_as_free_terms_and_years_are_understood():
    plan = _plan(QUESTIONS[1])
    roles = [(block["role"], block["label_en"]) for block in plan["blocks"]]
    assert ("free", "kefir") in roles
    assert plan["year_from"] == YEAR - 10 and plan["year_to"] is None
    compiled = compile_queries(plan, current_year=YEAR)["providers"]
    assert compiled["pubmed"]["query"].endswith(f"AND ({YEAR - 10}:3000[dp])")
    assert compiled["openalex"]["params"] == {"filter": f"from_publication_date:{YEAR - 10}-01-01"}
    assert compiled["crossref"]["params"] == {"filter": f"from-pub-date:{YEAR - 10}"}


def test_comparator_is_detected_and_left_out_of_the_string():
    plan = _plan(QUESTIONS[2])
    concepts = _concepts(plan)
    assert concepts["diet.plant_based"] == ("intervention", True)
    assert concepts["diet.mediterranean"] == ("comparator", False)
    assert concepts["design.systematic_review"] == ("design", True)
    pubmed = compile_queries(plan, current_year=YEAR)["providers"]["pubmed"]["query"]
    assert "mediterranean" not in pubmed
    assert "systematic[sb]" in pubmed and "meta-analysis[pt]" in pubmed
    assert {"code": "comparator_disabled", "block": "comparator:diet.mediterranean"} in plan["warnings"]


def test_related_concepts_are_merged_with_or():
    plan = _plan(QUESTIONS[4])
    keys = [block["key"] for block in plan["blocks"]]
    assert "population:age_group" in keys
    age = next(block for block in plan["blocks"] if block["key"] == "population:age_group")
    assert age["concept_ids"] == ["population.children", "population.adolescents"]
    assert (plan["year_from"], plan["year_to"]) == (2010, 2020)

    literacy = _plan(QUESTIONS[3])
    merged = next(b for b in literacy["blocks"] if b["key"] == "intervention:culinary_literacy")
    assert merged["concept_ids"] == ["care.food_literacy", "care.culinary"]
    assert literacy["year_from"] == 2015


def test_year_expressions():
    assert (_plan("diet before 2010")["year_to"]) == 2009
    assert (_plan("dieta e obesidade 2015-2023")["year_from"], _plan("dieta e obesidade 2015-2023")["year_to"]) == (2015, 2023)
    assert _plan("diet between 2000 and 2005")["year_from"] == 2000
    assert _plan("dieta nos últimos cinco anos")["year_from"] == YEAR - 5
    assert _plan("dieta até 2012")["year_to"] == 2012
    assert _plan("dieta 1850")["year_from"] is None


def test_typed_boolean_strings_are_passed_through_literally():
    for question in QUESTIONS[19:22]:
        plan = _plan(question)
        assert plan["mode"] == "manual"
        compiled = compile_queries(plan, current_year=YEAR)["providers"]
        for provider in ("pubmed", "europepmc", "openalex", "crossref"):
            assert compiled[provider]["query"] == question
    forced = _plan(QUESTIONS[20], detect_manual=False)
    assert forced["mode"] == "planned"
    assert {b["key"] for b in forced["blocks"]} >= {"population:glycemic_condition", "population:adiposity"}


def test_empty_and_noise_questions_are_explicit():
    assert _plan("")["warnings"] == [{"code": "empty_question"}]
    assert _plan("a b c de e")["warnings"] == [{"code": "nothing_recognised"}]
    assert {"code": "no_vocabulary_concepts"} in _plan("kefir kombucha")["warnings"]


def test_each_source_gets_its_own_syntax():
    plan = _plan(QUESTIONS[4])
    providers = compile_queries(plan, current_year=YEAR)["providers"]
    assert "[tiab]" in providers["pubmed"]["query"] and "(2010:2020[dp])" in providers["pubmed"]["query"]
    assert "TITLE_ABS:" in providers["europepmc"]["query"] and "PUB_YEAR:[2010 TO 2020]" in providers["europepmc"]["query"]
    assert "[tiab]" not in providers["openalex"]["query"] and "*" not in providers["openalex"]["query"]
    assert " AND " not in providers["crossref"]["query"] and " OR " not in providers["crossref"]["query"]
    assert 'tw:"obesidade"' in providers["bvs_lilacs"]["query"] and "tw:adolescent$" in providers["bvs_lilacs"]["query"]
    assert "obesidade" in providers["scielo"]["query"] and "adolescent$" in providers["scielo"]["query"]
    assert providers["bvs_lilacs"]["site_url"].startswith("https://pesquisa.bvsalud.org/portal/?lang=pt&q=")
    assert providers["scielo"]["site_url"].startswith("https://search.scielo.org/?lang=pt&q=")
    assert providers["pubmed"]["params"] == {"sort": "relevance"}

    broad = compile_queries(plan, field_mode="broad", current_year=YEAR)["providers"]
    assert "[tiab]" not in broad["pubmed"]["query"]
    assert broad["europepmc"]["params"] == {"synonym": "true"}
    assert "pubmed_automatic_term_mapping" in broad["pubmed"]["notes"]


def test_portuguese_terms_reach_international_sources_only_on_request():
    plan = _plan(QUESTIONS[0])
    default = compile_queries(plan, current_year=YEAR)["providers"]["openalex"]["query"]
    with_pt = compile_queries(plan, include_pt=True, current_year=YEAR)["providers"]["openalex"]["query"]
    assert "dieta mediterrânea" not in default
    assert "dieta mediterrânea" in with_pt


def test_edited_plans_compile_from_what_the_user_kept():
    plan = _plan(QUESTIONS[0])
    for block in plan["blocks"]:
        if block["role"] == "outcome":
            block["enabled"] = False
        if block["key"] == "intervention:diet.mediterranean":
            block["terms"][1]["enabled"] = False
            block["terms"].append({"text": "MedDiet", "lang": "en"})
    pubmed = compile_queries(plan, current_year=YEAR)["providers"]["pubmed"]["query"]
    assert "glycemic" not in pubmed
    assert "mediterranean dietary pattern" not in pubmed
    assert '"MedDiet"[tiab]' in pubmed


def test_plan_feeds_the_hosted_structured_review_compiler():
    spec = importlib.util.spec_from_file_location("nutev_web_query_compiler_planner", ROOT / "apps" / "nutev-web" / "query_compiler.py")
    assert spec and spec.loader
    compiler = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = compiler
    spec.loader.exec_module(compiler)
    for question in QUESTIONS[:17]:
        strategy = to_review_strategy(_plan(question))
        if strategy is None:
            continue
        compiled = compiler.compile_query_plan(question, ["pubmed", "europepmc", "openalex"], strategy)
        assert compiled["mode"] == "structured_review"
        assert compiled["controlled_vocabulary_terms"] == 0
        assert compiled["provider_queries"]["pubmed"]["query"]


def test_planning_is_deterministic():
    first = [_plan(q) for q in QUESTIONS]
    second = [_plan(q) for q in QUESTIONS]
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


# ----------------------------------------------------------------------- parity


def test_python_and_browser_planner_are_identical():
    encode_probe = ["a b&c=d/é", "(x OR y) AND \"z\"[tiab]", "filter[db_cluster][]", "~*'()!-_."]
    js = _run_harness(
        {"planner": {"questions": QUESTIONS, "currentYear": YEAR, "options": OPTIONS, "encode": encode_probe}}
    )
    assert js["encoded"] == [encode_component(value) for value in encode_probe]
    for question, item in zip(QUESTIONS, js["planner"]):
        plan = _plan(question)
        assert item["plan"] == plan, question
        for option, compiled in zip(OPTIONS, item["compiled"]):
            expected = compile_queries(
                plan,
                field_mode=option["fieldMode"],
                include_pt=option["includePt"],
                current_year=YEAR,
            )
            assert compiled == expected, (question, option)


def test_browser_respects_manual_override():
    js = _run_harness(
        {"planner": {"questions": [QUESTIONS[20]], "currentYear": YEAR, "options": [], "detectManual": False}}
    )
    assert js["planner"][0]["plan"] == _plan(QUESTIONS[20], detect_manual=False)


def test_every_planner_code_has_interface_text_in_both_languages():
    i18n = (ROOT / "apps" / "nutev-open" / "i18n.js").read_text(encoding="utf-8")
    codes: set[str] = {"warn.no_enabled_blocks", "warn.empty_question", "warn.nothing_recognised"}
    for question in QUESTIONS + ["kefir kombucha"]:
        plan = _plan(question)
        codes.update(f"warn.{w['code']}" for w in plan["warnings"])
        for mode in ("title_abstract", "broad"):
            for provider, item in compile_queries(plan, field_mode=mode, current_year=YEAR)["providers"].items():
                codes.add(f"dialect.{item['dialect']}")
                codes.update(f"note.{note}" for note in item["notes"] if note != "link_only")
                codes.add(f"strategy.open.{provider}")
    for role in VOCABULARY["roles"]:
        assert VOCABULARY["roles"][role]["label_pt"] and VOCABULARY["roles"][role]["label_en"]
    missing = sorted(code for code in codes if i18n.count(f'"{code}":') != 2)
    assert not missing, missing


def test_planner_module_is_offline():
    source = (ROOT / "apps" / "nutev-open" / "planner.js").read_text(encoding="utf-8")
    assert "fetch(" not in source and "XMLHttpRequest" not in source
    python = (ROOT / "src" / "nutev" / "search" / "question_planner.py").read_text(encoding="utf-8")
    assert "requests" not in python and "urllib.request" not in python
