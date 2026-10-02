"""Contracts for the Open Evidence Explorer (apps/nutev-open).

The explorer is a public, login-free browser surface. These tests prove that:

* its data bundle is generated from the canonical taxonomy/config (no drift);
* the JavaScript port classifies records exactly like the Python Reference
  Engine (traceability A/B/Q, identity, dedupe, taxonomy, score, document class);
* source adapters keep the same identifiers/URLs as the Python adapters;
* the page stays static, read-only and free of private/back-end surfaces.
"""

from __future__ import annotations

from datetime import datetime
import importlib.util
import json
from pathlib import Path
import re
import subprocess
from typing import Any

from nutev.audit_guardrails import annotate_record, record_traceability
from nutev.reference_identity import (
    canonical_identity,
    dedupe_records,
    normalize_doi,
    normalize_pmcid,
    normalize_pmid,
    normalize_title,
    normalize_url,
)
from nutev.search.classification import _classification_source
from nutev.search.crossref import _normalize_crossref_item
from nutev.search.europepmc import _normalize_result as _normalize_europepmc
from nutev.search.openalex import _normalize_openalex_item
from nutev.search.pubmed import _normalize_summary as _normalize_pubmed
from nutev.taxonomy import _norm, load_canonical_taxonomy

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "apps" / "nutev-open"
CONFIG = ROOT / "config"
HARNESS = ROOT / "nutev_tests" / "fixtures" / "open_explorer_harness.cjs"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rank_references = _load_module("rank_references_open", ROOT / "tools" / "rank_references.py")
build_open_explorer_data = _load_module(
    "build_open_explorer_data", ROOT / "tools" / "build_open_explorer_data.py"
)


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


# --------------------------------------------------------------------- fixtures

ROWS: list[dict[str, Any]] = [
    {
        "source": "europepmc",
        "source_provider": "europepmc",
        "title": "Mediterranean diet and type 2 diabetes remission: a systematic review and meta-analysis",
        "abstract": "Lifestyle medicine and nutrition care improved glycemic control, HbA1c and body weight.",
        "keywords": "dietary pattern; diabetes remission",
        "doi": "10.1000/ABC.123",
        "pmid": "31234567",
        "year": "2023",
        "provider_query": "mediterranean diet diabetes",
    },
    {
        "source": "openalex",
        "source_provider": "openalex",
        "title": "Mediterranean diet and type 2 diabetes remission",
        "abstract": (
            "Lifestyle medicine and nutrition care improved glycemic control, HbA1c and body weight "
            "in adults with type 2 diabetes following a mediterranean dietary pattern for 12 months."
        ),
        "doi": "https://doi.org/10.1000/abc.123",
        "year": 2023,
        "provider_query": "mediterranean diet diabetes",
    },
    {
        "source": "pubmed",
        "source_provider": "pubmed",
        "title": "Mediterranean diet and T2D remission (PubMed record)",
        "pmid": "31234567",
        "year": "2023",
    },
    {
        "source": "crossref",
        "source_provider": "crossref",
        "title": "Ultra-processed food intake and obesity in adolescents",
        "abstract": "Food processing (NOVA) and adiposity; waist circumference and BMI.",
        "doi": "10.5555/upf.2020.01).",
        "year": "2020",
    },
    {
        "source": "crossref",
        "source_provider": "crossref",
        "title": "Food environment and access policies: a framework",
        "doi": "10.12/too-short",
        "url": "https://www.Example.org/food/env/#section",
        "year": "2015",
    },
    {
        "source": "crossref",
        "source_provider": "crossref",
        "title": "Record with malformed DOI only",
        "doi": "not-a-doi",
    },
    {
        "source": "pubmed",
        "source_provider": "pubmed",
        "title": "Plant-based diets and cardiovascular risk: randomized controlled trial",
        "pmid": "12345678901",
        "pmcid": "pmc998877",
        "summary": "LDL cholesterol and blood pressure decreased with a whole food plant-based diet.",
        "publication_date": "Published 2019-05",
    },
    {"source": "europepmc", "source_provider": "europepmc", "title": "", "doi": "10.1000/no-title"},
    {"source": "", "source_provider": "", "title": "Missing provider", "doi": "10.1000/no-provider"},
    {"source": "doaj", "source_provider": "doaj", "title": "FTP only record", "url": "ftp://files.example.org/a.pdf"},
    {
        "source": "official",
        "source_provider": "Official Sources BR",
        "title": "Clinical practice guideline for hypertension: lifestyle nutrition and DASH",
        "url": "http://WWW.Site.gov.br/Guia/?b=2&a=1#top",
        "year": "1899",
        "date": "2021-03-01",
    },
    {
        "source": "crossref",
        "source_provider": "crossref",
        "title": "Conflicting record A",
        "doi": "10.7777/conflict.a",
        "url": "https://shared.example.org/landing",
    },
    {
        "source": "crossref",
        "source_provider": "crossref",
        "title": "Conflicting record B",
        "doi": "10.7777/conflict.b",
        "url": "https://shared.example.org/landing/",
    },
    {
        "source": "scielo",
        "source_provider": "scielo",
        "title": "Dieta mediterrânea e letramento alimentar em adultos com obesidade",
        "abstract": "Habilidades culinárias, comensalidade e alimentação saudável na atenção primária.",
        "keywords": ["Nutrição", "Culinária", "Straße"],
        "doi": "10.1590/s0102-311x2010000100001",
        "year": "2010",
    },
    {
        "source": "semantic_scholar",
        "source_provider": "Semantic Scholar",
        "title": "Food literacy and culinary skills: a behavior change framework for shared decision making",
        "keywords": "lifestyle nutrition, social determinants of health",
        "abstract": "Food-based dietary guideline adoption and nutrition care in primary care.",
        "doi": "doi:10.2222/FL.2024.7",
        "year": "2024",
    },
    {
        "source": "europepmc",
        "source_provider": "europepmc",
        "title": "Consensus statement on standards of care for lifestyle medicine",
        "abstract": "Position statement and scientific statement on physical activity, sleep and stress.",
        "pmid": 34567,
        "year": "2018",
    },
    {
        "source": "openalex",
        "source_provider": "openalex",
        "title": "A recommendation framework for practice guideline adoption",
        "url": "https://openalex.org/W123",
        "year": "2022",
    },
    {
        "source": "openalex",
        "source_provider": "openalex",
        "title": "Tie record beta",
        "url": "https://tie.example.org/b",
        "year": "2005",
    },
    {
        "source": "openalex",
        "source_provider": "openalex",
        "title": "Tie record alpha",
        "url": "https://tie.example.org/a",
        "year": "2005",
    },
    {
        "source": "pubmed",
        "source_provider": "pubmed",
        "title": "Time-restricted eating, chrononutrition and fasting glucose",
        "abstract": "Meal timing improved insulin resistance and postprandial glucose.",
        "pmid": "40000001",
        "pmcid": "PMC40000001",
        "year": str(datetime.now().year),
    },
]

PROBES: dict[str, list[Any]] = {
    "doi": [
        "10.1000/ABC.123",
        " https://doi.org/10.1000/xyz). ",
        "HTTP://DX.DOI.ORG/10.1000/Upper",
        "doi:10.1000/a b",
        "10.12/short",
        "10.123456789/long-registrant",
        "10.1234567890/too-long",
        "",
        None,
        0,
        12345,
    ],
    "pmid": ["123", " 0045 ", "1234567890", "12a", 34567, "", None, "123.0"],
    "pmcid": ["PMC123", "pmc456", "PMC", "PMC12a", " PMC789 ", 789, None],
    "url": [
        "https://www.Example.org/path/#frag",
        "HTTP://WWW.Site.gov.br/Guia/?b=2&a=1#top",
        "https://example.org",
        "https://example.org/a//",
        "https://user:pw@Host.org:8080/x?",
        "ftp://example.org/file",
        "mailto:someone@example.org",
        "//example.org/no-scheme",
        "https:///missing-host",
        "https://[::1]:8443/ipv6",
        "https://[bad/ipv6",
        "  https://padded.example.org/x  ",
        "https://ex\tample.org/tab",
        "",
        None,
    ],
    "title": ["  Dieta   Mediterrânea\tE  Saúde ", "ＦＵＬＬＷＩＤＴＨ title", "Straße", ""],
    "norm": [
        "Meta-Analysis of Ação/Nutrição",
        "Straße – Food’s “environment”",
        ["Nutrição", "Culinária"],
        "ﬁbre ﬂow",
        "  multiple   spaces\n",
        None,
        0,
        2024,
    ],
}

DOCUMENT_CLASS_PROBES: list[dict[str, Any]] = [
    {"article_type": "Randomized Controlled Trial; Journal Article", "title": "Diet trial"},
    {"article_type": "journal-article", "title": "A systematic review of DASH"},
    {"article_type": "article", "title": "Cohort", "abstract": "A prospective cohort of adults."},
    {"article_type": "peer-review", "title": "Report"},
    {"title": "Focus group study", "abstract": "Semi-structured interview and qualitative research."},
    {"title": "Untitled observation"},
    {"type": "Practice Guideline", "title": "x"},
    {"title": "Scoping review of food literacy instruments", "abstract": "meta-analysis not done"},
]


def _python_pipeline(rows: list[dict[str, Any]]) -> dict[str, Any]:
    taxonomy, metadata = load_canonical_taxonomy(CONFIG)
    profile = json.loads((CONFIG / "reference_mode.json").read_text(encoding="utf-8"))
    guardrails = rank_references._guardrail_policy(profile)
    annotated = [annotate_record(row) for row in rows]
    eligible = [row for row in annotated if not row["audit_quarantined"]]
    quarantined = [row for row in annotated if row["audit_quarantined"]]
    unique = dedupe_records(eligible)
    ranked = [
        rank_references.score_record(
            row,
            taxonomy,
            list(profile.get("focus_keywords") or []),
            dict(profile.get("provider_weights") or {}),
            guardrails,
            list(metadata.get("primary_dimension_order") or []),
        )
        for row in unique
    ]
    ranked.sort(
        key=lambda row: (
            -float(row.get("reference_score") or 0),
            -int(row.get("reference_year") or 0),
            str(row.get("title") or ""),
        )
    )
    for index, row in enumerate(ranked):
        row["reference_rank"] = index + 1
    rank_references._assign_taxonomy_ranks(ranked)
    return {"unique": unique, "ranked": ranked, "quarantined": quarantined}


COMPARED_FIELDS = (
    "title",
    "reference_rank",
    "reference_score",
    "score_breakdown",
    "taxonomy_primary",
    "taxonomy_secondary",
    "taxonomy_dimensions",
    "taxonomy_groups",
    "taxonomy_group_scores",
    "matched_terms",
    "focus_keyword_hits",
    "document_type_hits",
    "document_type_applied",
    "reference_year",
    "reference_provider",
    "taxonomy_ranks",
    "taxonomy_primary_rank",
    "audit_traceability",
    "audit_reasons",
    "doi",
    "pmid",
    "pmcid",
    "url",
)


# --------------------------------------------------------------------- bundle


def test_bundle_is_generated_from_canonical_sources():
    assert build_open_explorer_data.main(["--check"]) == 0


def test_bundle_matches_canonical_taxonomy_exactly():
    taxonomy, metadata = load_canonical_taxonomy(CONFIG)
    bundle = build_open_explorer_data.build_bundle()
    groups = {group["id"]: group for group in bundle["taxonomy"]["groups"]}
    assert list(groups) == list(taxonomy)
    for group_id, terms in taxonomy.items():
        assert groups[group_id]["terms"] == terms
        assert groups[group_id]["label_en"]
        assert groups[group_id]["label_pt"]
    assert bundle["taxonomy_version"] == metadata["taxonomy_version"]
    assert bundle["taxonomy"]["primary_dimension_order"] == metadata["primary_dimension_order"]
    family_ids = {family["id"] for family in bundle["taxonomy"]["families"]}
    assert {group["family"] for group in groups.values()} <= family_ids


def test_bundle_scoring_constants_follow_reference_mode():
    profile = json.loads((CONFIG / "reference_mode.json").read_text(encoding="utf-8"))
    scoring = build_open_explorer_data.build_bundle()["scoring"]
    assert scoring["focus_keywords"] == profile["focus_keywords"]
    assert scoring["provider_weights"] == {k: float(v) for k, v in profile["provider_weights"].items()}
    assert scoring["taxonomy_score_cap"] == float(profile["guardrails"]["taxonomy_score_cap"])
    assert scoring["focus_score_cap"] == float(profile["guardrails"]["focus_score_cap"])


# --------------------------------------------------------------------- parity


def test_identifier_normalization_parity():
    js = _run_harness({"probes": PROBES})["probes"]
    assert js["doi"] == [normalize_doi(value) for value in PROBES["doi"]]
    assert js["pmid"] == [normalize_pmid(value) for value in PROBES["pmid"]]
    assert js["pmcid"] == [normalize_pmcid(value) for value in PROBES["pmcid"]]
    assert js["url"] == [normalize_url(value) for value in PROBES["url"]]
    assert js["title"] == [normalize_title(value) for value in PROBES["title"]]
    assert js["norm"] == [_norm(value) for value in PROBES["norm"]]


def test_traceability_identity_and_document_class_parity():
    js = _run_harness(
        {
            "probes": {
                "traceability": ROWS,
                "identity": ROWS,
                "document_class": DOCUMENT_CLASS_PROBES,
            }
        }
    )["probes"]
    assert js["traceability"] == [list(record_traceability(row)) for row in ROWS]
    assert js["identity"] == [canonical_identity(row) for row in ROWS]
    expected_classes = []
    for row in DOCUMENT_CLASS_PROBES:
        document_class, confidence, signals = _classification_source(row)
        expected_classes.append([document_class, confidence, signals])
    assert js["document_class"] == expected_classes
    traceability = {value[0] for value in js["traceability"]}
    assert traceability == {
        "A_IDENTIFIER",
        "B_TRACEABLE_URL",
        "Q_INCOMPLETE_ORIGIN",
        "Q_INVALID_IDENTIFIER",
        "Q_UNTRACEABLE",
    }


def test_pipeline_parity_with_reference_engine():
    now_year = datetime.now().year
    expected = _python_pipeline(ROWS)
    js = _run_harness({"rows": ROWS, "nowYear": now_year})["pipeline"]

    assert [
        [row.get("title") or "", row["audit_traceability"], row["audit_reasons"]]
        for row in expected["quarantined"]
    ] == js["quarantined"]

    assert len(js["ranked"]) == len(expected["ranked"])
    for py_row, js_row in zip(expected["ranked"], js["ranked"]):
        for field in COMPARED_FIELDS:
            assert js_row.get(field) == py_row.get(field), (field, py_row.get("title"))

    py_provenance = sorted(
        (canonical_identity(row), tuple(row.get("source_providers") or [])) for row in expected["unique"]
    )
    js_provenance = sorted(
        (canonical_identity(row), tuple(row.get("source_providers") or [])) for row in js["ranked"]
    )
    assert js_provenance == py_provenance

    stats = js["stats"]
    assert stats["retrieved_rows"] == len(ROWS)
    assert stats["quarantined"] == len(expected["quarantined"])
    assert stats["unique_ranked"] == len(expected["ranked"])
    assert stats["duplicates_merged"] == len(ROWS) - len(expected["quarantined"]) - len(expected["ranked"])
    assert stats["duplicates_merged"] >= 2, "fixture must exercise DOI and PMID bridging"
    assert sum(stats["levels"].values()) == stats["works"]


# --------------------------------------------------------------------- adapters

EUROPEPMC_ITEM = {
    "id": "31234567",
    "source": "MED",
    "pmid": "31234567",
    "pmcid": "PMC456",
    "doi": "10.1000/abc.123",
    "title": "<i>Mediterranean</i> diet &amp; remission",
    "authorString": "Silva A, Souza B.",
    "journalInfo": {"yearOfPublication": 2022, "journal": {"title": "Nutrients"}},
    "pubYear": "2022",
    "abstractText": "<h4>Background</h4>Diet &amp; glycemic control.",
    "pubTypeList": {"pubType": ["Review", "Journal Article"]},
    "keywordList": {"keyword": ["diet", "diabetes"]},
    "isOpenAccess": "Y",
    "firstPublicationDate": "2022-03-01",
    "fullTextUrlList": {"fullTextUrl": [{"url": "https://europepmc.org/articles/PMC456"}]},
}

OPENALEX_ITEM = {
    "id": "https://openalex.org/W1",
    "doi": "https://doi.org/10.2/plant",
    "display_name": "Plant-based diets",
    "publication_year": 2021,
    "publication_date": "2021-01-02",
    "type": "article",
    "ids": {
        "pmid": "https://pubmed.ncbi.nlm.nih.gov/999",
        "pmcid": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC77",
    },
    "primary_location": {"landing_page_url": "https://journal.org/a", "source": {"display_name": "Appetite"}},
    "authorships": [{"author": {"display_name": "Ana Lima"}}, {"author": {"display_name": "Bo Chen"}}],
    "abstract_inverted_index": {"Plant": [0], "diets": [1, 3], "and": [2]},
    "open_access": {"is_oa": True, "oa_url": "https://journal.org/a.pdf"},
    "keywords": [{"display_name": "Diet"}],
}

CROSSREF_ITEM = {
    "DOI": "10.3/food",
    "title": ["Food literacy"],
    "abstract": "<jats:p>Cooking <jats:italic>skills</jats:italic>.</jats:p>",
    "author": [{"given": "Ana", "family": "Lima"}],
    "container-title": ["Appetite"],
    "type": "journal-article",
    "published-print": {"date-parts": [[2020, 5]]},
    "link": [{"URL": "https://x.org/article.pdf", "content-type": "application/pdf"}],
}

PUBMED_ITEM = {
    "uid": "111",
    "pubdate": "2019 Jan",
    "source": "Nutr J",
    "fulljournalname": "Nutrition journal",
    "title": "DASH diet and blood pressure.",
    "authors": [{"name": "Smith J"}, {"name": "Doe A"}],
    "articleids": [
        {"idtype": "pubmed", "value": "111"},
        {"idtype": "doi", "value": "10.4/dash"},
        {"idtype": "pmc", "value": "PMC5"},
    ],
    "pubtype": ["Journal Article", "Randomized Controlled Trial"],
    "elocationid": "doi: 10.4/dash",
    "_abstract": "Abstract text.",
}


def test_source_adapters_keep_python_identifiers_and_urls():
    api = _run_harness(
        {"api": {"europepmc": [EUROPEPMC_ITEM], "openalex": [OPENALEX_ITEM], "crossref": [CROSSREF_ITEM], "pubmed": [PUBMED_ITEM]}}
    )["api"]

    epmc = api["europepmc"][0]
    py_epmc = _normalize_europepmc(EUROPEPMC_ITEM)
    for field in ("source", "source_provider", "doi", "pmid", "pmcid", "url", "year", "authors", "publication_date"):
        assert epmc[field] == py_epmc[field], field
    assert epmc["title"] == "Mediterranean diet & remission"
    assert epmc["abstract"] == "Background Diet & glycemic control."
    assert epmc["journal"] == "Nutrients"
    assert epmc["article_type"] == "Review; Journal Article"
    assert epmc["keywords"] == "diet; diabetes"

    openalex = api["openalex"][0]
    py_openalex = _normalize_openalex_item(OPENALEX_ITEM, "q")
    for field in ("source", "doi", "url", "pmcid", "journal", "publication_date", "article_type", "authors"):
        assert openalex[field] == py_openalex[field], field
    assert openalex["year"] == str(py_openalex["year"])
    assert openalex["abstract"] == "Plant diets and diets"
    assert openalex["pmid"] == "999"

    crossref = api["crossref"][0]
    py_crossref = _normalize_crossref_item(CROSSREF_ITEM, "q")
    for field in ("source", "doi", "url", "journal", "year", "publication_date", "article_type", "authors"):
        assert crossref[field] == py_crossref[field], field
    assert crossref["abstract"] == "Cooking skills."

    pubmed = api["pubmed"][0]
    py_item = {key: value for key, value in PUBMED_ITEM.items() if key != "_abstract"}
    py_pubmed = _normalize_pubmed(py_item, "111", "q")
    for field in ("source", "doi", "pmid", "pmcid", "url", "journal", "year", "publication_date", "article_type", "authors"):
        assert pubmed[field] == py_pubmed[field], field
    assert pubmed["abstract"] == "Abstract text."

    for row in (epmc, openalex, crossref, pubmed):
        assert row["provider_query"] == "q"
        assert row["retrieved_at"] == "t"

    urls = api["urls"]
    assert urls["europepmc"].startswith("https://www.ebi.ac.uk/europepmc/webservices/rest/search?")
    assert "query=diet+%26+health" in urls["europepmc"]
    assert urls["openalex"].startswith("https://api.openalex.org/works?")
    assert urls["crossref"].startswith("https://api.crossref.org/works?")


# --------------------------------------------------------------------- public surface guardrails

ALLOWED_CONNECT = {
    "https://www.ebi.ac.uk",
    "https://api.openalex.org",
    "https://api.crossref.org",
    "https://eutils.ncbi.nlm.nih.gov",
}


def _app_text_files() -> list[Path]:
    return sorted(
        path
        for path in APP.rglob("*")
        if path.is_file() and path.suffix in {".html", ".js", ".css", ".json", ".md"}
    )


def test_page_is_static_with_restrictive_csp():
    html = (APP / "index.html").read_text(encoding="utf-8")
    csp = re.search(r'http-equiv="Content-Security-Policy"\s+content="([^"]+)"', html)
    assert csp, "index.html must declare a Content-Security-Policy"
    directives = dict(
        (part.strip().split(" ", 1) + [""])[:2] for part in csp.group(1).split(";") if part.strip()
    )
    assert directives["default-src"] == "'self'"
    assert directives["script-src"] == "'self'"
    assert set(directives["connect-src"].split()) == {"'self'"} | ALLOWED_CONNECT
    assert "object-src" in directives and directives["object-src"] == "'none'"
    for src in re.findall(r'<script[^>]+src="([^"]+)"', html):
        assert not re.match(r"^(https?:)?//", src), src
    assert "<form" not in html.lower() or 'method="post"' not in html.lower()


def test_explorer_has_no_private_backend_or_model_surfaces():
    forbidden = [
        r"/api/",
        r"agent[-_]context",
        r"project_output_reference",
        r"ResearchApplication",
        r"api\.openai\.com",
        r"api\.anthropic\.com",
        r"generativelanguage",
        r"localStorage\.setItem\([^)]*(token|session|password)",
        r"method:\s*['\"]POST",
        r"document\.cookie",
        r"\beval\(",
        r"new Function\(",
    ]
    for path in _app_text_files():
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden:
            assert not re.search(pattern, text, re.IGNORECASE), (path.name, pattern)


def test_fetch_targets_are_only_open_source_apis():
    sources = (APP / "sources.js").read_text(encoding="utf-8")
    hosts = set(re.findall(r'"(https://[a-z0-9.-]+)/', sources))
    request_hosts = {
        host
        for host in hosts
        if any(marker in host for marker in ("api.", "eutils.", "ebi.ac.uk"))
    }
    assert request_hosts == ALLOWED_CONNECT
    app = (APP / "app.js").read_text(encoding="utf-8")
    assert "fetch(" not in app, "network access must stay inside sources.js"


def test_guardrail_language_is_visible_in_both_languages():
    html = (APP / "index.html").read_text(encoding="utf-8")
    i18n = (APP / "i18n.js").read_text(encoding="utf-8")
    combined = html + i18n
    for phrase in (
        "não representa qualidade metodológica",
        "does not represent methodological quality",
        "Scopus",
        "nunca são simulad",
        "never simulated",
        "Q_UNTRACEABLE",
        "A_IDENTIFIER",
        "B_TRACEABLE_URL",
    ):
        assert phrase in combined, phrase
    for banned in ("qualidade da evidência: alta", "evidence quality: high", "nível de evidência a"):
        assert banned not in combined.lower()
