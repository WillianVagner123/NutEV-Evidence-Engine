"""Pre-review of config/query_vocabulary.json for the human expert review.

Runs deterministic consistency checks and writes a worksheet (one row per concept) plus
a short report. It does NOT review meaning and never changes ``review_status``: only a
person with domain expertise can approve the vocabulary (see docs/review/).

    python tools/review_query_vocabulary.py          # regenerate the worksheet and report
    python tools/review_query_vocabulary.py --check  # fail if they are out of date
"""

from __future__ import annotations

import argparse
import csv
import io
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nutev.search.question_planner import (  # noqa: E402
    _trigger_index,
    load_query_vocabulary,
    tokens_of,
)

CONFIG_DIR = ROOT / "config"
REVIEW_DIR = ROOT / "docs" / "review"
WORKSHEET_PATH = REVIEW_DIR / "query_vocabulary_review.csv"
REPORT_PATH = REVIEW_DIR / "QUERY_VOCABULARY_PRE_REVIEW.md"

# Single words that, alone as a synonym, retrieve far beyond the concept.
BROAD_WORDS = frozenset({
    "health", "diet", "diets", "food", "foods", "nutrition", "care", "risk", "disease",
    "diseases", "eating", "lifestyle", "intervention", "interventions", "outcome", "outcomes",
    "saude", "dieta", "alimentacao", "alimentos", "nutricao", "cuidado", "doenca", "risco",
})
COLUMNS = (
    "concept_id", "role", "label_pt", "label_en", "default_enabled", "taxonomy_group",
    "triggers", "en_synonyms", "pt_terms", "pubmed_filters", "automatic_flags",
    "reviewer_decision", "reviewer_notes",
)
SEVERITY_ORDER = {"warn": 0, "info": 1}


def _join(values: Any) -> str:
    return " | ".join(str(value) for value in values or [])


def find_issues(vocabulary: dict[str, Any]) -> list[dict[str, str]]:
    """Deterministic, meaning-blind checks. Each finding is a prompt for the reviewer."""

    issues: list[dict[str, str]] = []

    def add(concept_id: str, severity: str, code: str, detail: str) -> None:
        issues.append({"concept_id": concept_id, "severity": severity, "code": code, "detail": detail})

    stopwords = {word for words in (vocabulary.get("stopwords") or {}).values() for word in tokens_of(" ".join(words))}

    # Same normalized trigger for two concepts: only one can ever be recognised.
    for entries in _trigger_index(vocabulary).values():
        owners: dict[tuple[str, ...], list[str]] = {}
        for key, concept_id in entries:
            owners.setdefault(key, []).append(concept_id)
        for key, concept_ids in owners.items():
            if len(concept_ids) > 1:
                winner, *losers = concept_ids
                for loser in losers:
                    add(loser, "warn", "trigger_shadowed",
                        f"trigger '{' '.join(key)}' also belongs to {winner}, which wins; this concept never sees it")

    synonym_owners: dict[str, list[str]] = {}
    for concept in vocabulary["concepts"]:
        cid = concept["id"]
        en = [str(term) for term in concept.get("en") or []]
        pt = [str(term) for term in concept.get("pt") or []]
        if not en:
            add(cid, "warn", "no_english_synonyms", "no English synonym: international sources get nothing for this block")
        if not pt and concept.get("role") != "design":
            add(cid, "info", "no_portuguese_terms", "no Portuguese term for BVS/LILACS and SciELO")
        folded = [term.casefold() for term in en]
        for term in sorted({term for term in folded if folded.count(term) > 1}):
            add(cid, "warn", "duplicate_synonym", f"'{term}' listed more than once")
        for term in en:
            synonym_owners.setdefault(term.casefold(), []).append(cid)
            words = tokens_of(term)
            if len(words) == 1 and words[0] in BROAD_WORDS:
                add(cid, "warn", "broad_single_word", f"'{term}' alone matches far beyond this concept")
            if len(term.replace("*", "")) <= 4 and term.isupper():
                add(cid, "info", "short_acronym", f"'{term}' is a short acronym; check it is unambiguous in titles/abstracts")
            if term.endswith("*"):
                add(cid, "info", "truncation", f"'{term}' is truncated: PubMed/Europe PMC truncate, OpenAlex drops the '*'")
        for trigger in concept.get("triggers") or []:
            words = tokens_of(trigger)
            if words and all(word in stopwords for word in words):
                add(cid, "warn", "stopword_trigger", f"trigger '{trigger}' is made only of stopwords")
            if words and len(words) == 1 and len(words[0]) <= 2:
                add(cid, "warn", "very_short_trigger", f"trigger '{trigger}' is one or two letters")
        if not concept.get("taxonomy_group") and concept.get("role") not in {"design"}:
            add(cid, "info", "no_taxonomy_axis", "not linked to a MEV/NEV taxonomy axis")

    for term, owners in sorted(synonym_owners.items()):
        unique = sorted(set(owners))
        if len(unique) > 1:
            for cid in unique:
                others = ", ".join(other for other in unique if other != cid)
                add(cid, "info", "shared_synonym", f"'{term}' is also a synonym of {others}")

    issues.sort(key=lambda item: (SEVERITY_ORDER[item["severity"]], item["concept_id"], item["code"], item["detail"]))
    return issues


def worksheet(vocabulary: dict[str, Any], issues: list[dict[str, str]]) -> str:
    flags: dict[str, list[str]] = {}
    for issue in issues:
        flags.setdefault(issue["concept_id"], []).append(f"{issue['severity']}:{issue['code']}")
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(COLUMNS)
    for concept in vocabulary["concepts"]:
        writer.writerow([
            concept["id"],
            concept.get("role", ""),
            concept.get("label_pt", ""),
            concept.get("label_en", ""),
            "yes" if concept.get("default_enabled", True) else "no",
            concept.get("taxonomy_group") or "",
            _join(concept.get("triggers")),
            _join(concept.get("en")),
            _join(concept.get("pt")),
            _join(concept.get("pubmed_filters")),
            _join(sorted(set(flags.get(concept["id"], [])))),
            "",
            "",
        ])
    return buffer.getvalue()


def report(vocabulary: dict[str, Any], issues: list[dict[str, str]]) -> str:
    warn = [issue for issue in issues if issue["severity"] == "warn"]
    info = [issue for issue in issues if issue["severity"] == "info"]
    counts: dict[str, int] = {}
    for issue in issues:
        counts[issue["code"]] = counts.get(issue["code"], 0) + 1
    lines = [
        "# Pré-revisão automática do vocabulário de busca",
        "",
        "> Arquivo gerado por `python tools/review_query_vocabulary.py`. Não editar à mão.",
        "",
        f"- Vocabulário: `{vocabulary.get('vocabulary_version')}`, {len(vocabulary['concepts'])} conceitos.",
        f"- Estado: `{vocabulary.get('review_status')}`. Esta pré-revisão **não** muda o estado; ela só aponta onde olhar.",
        f"- Achados: {len(warn)} avisos e {len(info)} observações.",
        "",
        "As verificações são mecânicas (gatilhos que se sobrepõem, sinônimos repetidos ou genéricos, siglas curtas, truncamento, falta de termos em português, conceitos sem eixo MEV/NEV). Elas não julgam significado. A planilha `query_vocabulary_review.csv` traz uma linha por conceito para a decisão do especialista; o procedimento está em `QUERY_VOCABULARY_REVIEW.md`.",
        "",
        "## Contagem por tipo",
        "",
        "| Código | Quantidade |",
        "| --- | --- |",
    ]
    lines += [f"| `{code}` | {count} |" for code, count in sorted(counts.items())]
    lines += ["", "## Avisos (olhar primeiro)", ""]
    if warn:
        lines += ["| Conceito | Código | Detalhe |", "| --- | --- | --- |"]
        lines += [f"| `{i['concept_id']}` | `{i['code']}` | {i['detail']} |" for i in warn]
    else:
        lines.append("Nenhum aviso.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if the worksheet or report is out of date")
    args = parser.parse_args()
    vocabulary = load_query_vocabulary(CONFIG_DIR)
    issues = find_issues(vocabulary)
    outputs = {WORKSHEET_PATH: worksheet(vocabulary, issues), REPORT_PATH: report(vocabulary, issues)}
    if args.check:
        stale = [path for path, text in outputs.items() if not path.is_file() or path.read_text(encoding="utf-8") != text]
        if stale:
            print("out of date: " + ", ".join(str(path.relative_to(ROOT)) for path in stale) + " (run tools/review_query_vocabulary.py)")
            return 1
        print("vocabulary pre-review files match config/query_vocabulary.json")
        return 0
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    for path, text in outputs.items():
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
