from __future__ import annotations

import json
from pathlib import Path


MODE_LIMIT = {"quick": 3, "thesis": 6, "exhaustive": 10}


def load_keyword_taxonomy(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def or_group(terms, max_terms=None):
    terms = [t for t in (terms or []) if t]
    if max_terms:
        terms = terms[:max_terms]
    return "(" + " OR ".join(terms) + ")" if terms else ""


def and_group(groups):
    groups = [g for g in groups if g]
    return " AND ".join(groups)


def _core(taxonomy):
    return ["nutrition", "diet", "lifestyle", "obesity", "cardiometabolic"] + taxonomy.get("controlled_vocabulary", {}).get("mesh_dec", [])[:8]


def _mk(intent, workstream, mode, terms, taxonomy):
    lim = MODE_LIMIT.get(mode, 6)
    neg = taxonomy.get("negative_noise_terms", [])[:8]
    q = and_group([or_group(terms, lim), "(obesity OR cardiometabolic)", "(diet OR nutrition OR lifestyle)", f"NOT {or_group(neg, min(6, len(neg)))}" if neg else ""])
    return {"intent": intent, "workstream": workstream, "query": q}


def build_guideline_queries(taxonomy, workstream, mode):
    terms = ["guideline", "clinical practice guideline", "consensus", "scientific statement"] + taxonomy.get("international_guideline_terms", {}).get("spanish", [])
    return [_mk("guideline", workstream, mode, terms, taxonomy)]


def build_review_queries(taxonomy, workstream, mode):
    return [_mk("review", workstream, mode, ["systematic review", "meta-analysis", "umbrella review"], taxonomy)]


def build_trial_queries(taxonomy, workstream, mode):
    return [_mk("trial", workstream, mode, ["randomized trial", "randomised trial", "pragmatic trial"], taxonomy)]


def build_official_queries(taxonomy, workstream, mode):
    inst = sum(taxonomy.get("institutions_societies", {}).values(), [])
    return [_mk("official", workstream, mode, inst or ["World Health Organization"], taxonomy)]


def build_instrument_queries(taxonomy, workstream, mode):
    return [_mk("instrument", workstream, mode, taxonomy.get("instrument_terms", []) + ["questionnaire", "instrument"], taxonomy)]


def build_update_queries(taxonomy, workstream, mode):
    return [_mk("update", workstream, mode, taxonomy.get("update_terms", []), taxonomy)]


def build_country_queries(taxonomy, workstream, mode):
    terms = taxonomy.get("institutions_societies", {}).get("brazil_latam", []) + taxonomy.get("institutions_societies", {}).get("europe", [])
    return [_mk("country", workstream, mode, terms, taxonomy)]


def build_smart_queries(taxonomy, workstreams, mode):
    out = {}
    for ws in workstreams:
        items = []
        items += build_guideline_queries(taxonomy, ws, mode)
        items += build_review_queries(taxonomy, ws, mode)
        items += build_trial_queries(taxonomy, ws, mode)
        if mode != "quick":
            items += build_official_queries(taxonomy, ws, mode)
            items += build_instrument_queries(taxonomy, ws, mode)
            items += build_update_queries(taxonomy, ws, mode)
        if mode == "exhaustive":
            items += build_country_queries(taxonomy, ws, mode)
        out[ws] = items
    return out
