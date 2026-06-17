"""Single source of truth for the NutEV taxonomy.

``config/taxonomy.json`` is the one file an editor touches to add/change a
concept (condition, diet, outcome, document type), its per-language synonyms,
its MeSH descriptor, its OpenAlex concept id and its scoring weight, plus the
classification ontology (domains/outcomes/evidence types).

``build_all`` regenerates the derived config files the pipeline already reads
(``multilingual_lexicon.json``, ``nutev_ontology.json``), seeds the OpenAlex
concept cache and merges concept scores into ``scoring_rules.json`` — so the
rest of the pipeline keeps consuming the same files and stays fully tested.
"""

from __future__ import annotations

import json
from pathlib import Path

TAXONOMY_FILENAME = "taxonomy.json"

# Concept type <-> multilingual_lexicon concept_group name. Order matters: it is
# the order groups/concepts are emitted in the generated lexicon.
_TYPE_TO_GROUP = {
    "condition": "conditions",
    "diet": "diets",
    "outcome": "outcomes",
    "doc_type": "doc_types",
}
_VALID_TYPES = list(_TYPE_TO_GROUP)


def load_taxonomy(config_root: str | Path) -> dict:
    """Load the master taxonomy; return {} if missing/invalid."""
    path = Path(config_root) / TAXONOMY_FILENAME
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _concepts(tax: dict) -> list[dict]:
    return [c for c in (tax.get("concepts") or []) if isinstance(c, dict) and c.get("id")]


def _ordered_concepts(tax: dict) -> list[dict]:
    """Concepts grouped by type in canonical order, preserving within-group order."""
    concepts = _concepts(tax)
    ordered: list[dict] = []
    for ctype in _VALID_TYPES:
        ordered.extend(c for c in concepts if c.get("type") == ctype)
    # Keep any concept with an unknown/missing type at the end (defensive).
    ordered.extend(c for c in concepts if c.get("type") not in _VALID_TYPES)
    return ordered


def build_multilingual_lexicon(tax: dict) -> dict:
    """Reconstruct the ``multilingual_lexicon.json`` structure from the master."""
    ordered = _ordered_concepts(tax)
    concept_groups: dict[str, list[str]] = {group: [] for group in _TYPE_TO_GROUP.values()}
    for concept in ordered:
        group = _TYPE_TO_GROUP.get(concept.get("type"))
        if group:
            concept_groups[group].append(concept["id"])
    mesh = {c["id"]: c["mesh"] for c in ordered if c.get("mesh")}
    concepts = {c["id"]: (c.get("terms") or {}) for c in ordered}
    return {
        "_comment": tax.get("lexicon_comment", ""),
        "languages": list(tax.get("languages") or []),
        "concept_groups": concept_groups,
        "mesh": mesh,
        "concepts": concepts,
    }


def build_ontology(tax: dict) -> dict:
    """The classification ontology is stored verbatim in the master."""
    ontology = tax.get("ontology")
    return ontology if isinstance(ontology, dict) else {}


def build_openalex_cache(tax: dict) -> dict[str, str]:
    """Term -> OpenAlex concept-id seed from concepts that declare an ``openalex`` id.

    Mirrors the cache format written by ``openalex_concepts.save_concept_cache``
    (lowercased term keys). Returns {} when no concept declares an id.
    """
    cache: dict[str, str] = {}
    for concept in _concepts(tax):
        concept_id = str(concept.get("openalex") or "").strip()
        if not concept_id:
            continue
        cache[str(concept["id"]).strip().lower()] = concept_id
        for term in (concept.get("terms") or {}).get("en", []) or []:
            cache.setdefault(str(term).strip().lower(), concept_id)
    return cache


def concept_scores(tax: dict) -> dict[str, int]:
    """Concept id -> score for concepts that declare a ``score`` (else {})."""
    scores: dict[str, int] = {}
    for concept in _concepts(tax):
        if concept.get("score") is not None:
            try:
                scores[str(concept["id"])] = int(concept["score"])
            except (TypeError, ValueError):
                continue
    return scores


def validate_taxonomy(tax: dict) -> list[str]:
    """Return a list of human-readable problems ([] means valid)."""
    errors: list[str] = []
    if not tax:
        return ["taxonomy.json is missing or invalid JSON"]
    if not isinstance(tax.get("languages"), list) or not tax["languages"]:
        errors.append("'languages' must be a non-empty list")
    languages = tax.get("languages") or []
    concepts = tax.get("concepts")
    if not isinstance(concepts, list) or not concepts:
        errors.append("'concepts' must be a non-empty list")
        concepts = []
    seen: set[str] = set()
    for i, concept in enumerate(concepts):
        if not isinstance(concept, dict):
            errors.append(f"concept #{i} is not an object")
            continue
        cid = concept.get("id")
        if not cid:
            errors.append(f"concept #{i} has no 'id'")
            continue
        if cid in seen:
            errors.append(f"duplicate concept id: {cid!r}")
        seen.add(cid)
        if concept.get("type") not in _VALID_TYPES:
            errors.append(f"concept {cid!r} has invalid type {concept.get('type')!r} (use {_VALID_TYPES})")
        terms = concept.get("terms")
        if not isinstance(terms, dict) or not terms.get("en"):
            errors.append(f"concept {cid!r} must have at least one English term in 'terms.en'")
            continue
        missing = [lang for lang in languages if not terms.get(lang)]
        if missing:
            errors.append(f"concept {cid!r} is missing terms for languages: {missing}")
    ontology = tax.get("ontology")
    if not isinstance(ontology, dict) or "domains" not in ontology or "evidence_types" not in ontology:
        errors.append("'ontology' must contain at least 'domains' and 'evidence_types'")
    return errors


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_all(config_root: str | Path) -> dict[str, Path]:
    """Regenerate every derived config file from the master. Returns written paths.

    Non-destructive by default: ``scoring_rules.json`` and the OpenAlex cache are
    only touched when concepts actually declare scores / ids, and only those
    entries are added (other content is preserved).
    """
    config_root = Path(config_root)
    tax = load_taxonomy(config_root)
    errors = validate_taxonomy(tax)
    if errors:
        raise ValueError("taxonomy.json is invalid:\n  - " + "\n  - ".join(errors))

    written: dict[str, Path] = {}

    lexicon_path = config_root / "multilingual_lexicon.json"
    _write_json(lexicon_path, build_multilingual_lexicon(tax))
    written["multilingual_lexicon"] = lexicon_path

    ontology_path = config_root / "nutev_ontology.json"
    _write_json(ontology_path, build_ontology(tax))
    written["nutev_ontology"] = ontology_path

    # OpenAlex concept cache: merge declared ids into the existing cache.
    seed = build_openalex_cache(tax)
    if seed:
        from nutev.search.openalex_concepts import load_concept_cache, save_concept_cache

        cache = load_concept_cache(config_root)
        cache.update(seed)
        save_concept_cache(config_root, cache)
        written["openalex_concepts"] = config_root / "openalex_concepts.json"

    # Concept scores: merge into scoring_rules.json keyword_points (additive).
    scores = concept_scores(tax)
    scoring_path = config_root / "scoring_rules.json"
    if scores and scoring_path.exists():
        scoring = json.loads(scoring_path.read_text(encoding="utf-8"))
        keyword_points = dict(scoring.get("keyword_points") or {})
        changed = False
        for term, score in scores.items():
            if keyword_points.get(term) != score:
                keyword_points[term] = score
                changed = True
        if changed:
            scoring["keyword_points"] = keyword_points
            _write_json(scoring_path, scoring)
            written["scoring_rules"] = scoring_path

    return written


def concept_summary(tax: dict) -> dict[str, list[str]]:
    """Concept ids grouped by type, for `nutev taxonomy list`."""
    summary: dict[str, list[str]] = {ctype: [] for ctype in _VALID_TYPES}
    for concept in _concepts(tax):
        summary.setdefault(concept.get("type", "other"), []).append(concept["id"])
    return summary
