from __future__ import annotations

from pathlib import Path

import pandas as pd

from nutev.export.excel_writer import write_excel_file, write_excel_sheet


def _write_workbook_or_csv(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with pd.ExcelWriter(path) as writer:
            for name, frame in sheets.items():
                write_excel_sheet(writer, frame, name)
    except Exception:
        for name, frame in sheets.items():
            frame.to_csv(path.with_suffix(f".{name[:31]}.csv"), index=False, encoding="utf-8-sig")
        path.touch()
from nutev.search.normalize import (
    infer_clinical_condition,
    infer_diet_pattern,
    infer_doc_type,
    infer_year,
    normalize_source,
)

DIET_PATTERNS = [
    "mediterranean",
    "dash",
    "keto",
    "ketogenic",
    "vegetarian",
    "vegan",
    "plant-based",
    "low-carb",
]
CLINICAL_CONDITIONS = [
    "diabetes",
    "hypertension",
    "dyslipidemia",
    "cardiovascular",
    "metabolic syndrome",
    "nafld",
    "masld",
]
NUTEV_OBJECT_RULES = {
    "evidence_table": ["trial", "meta", "review", "cohort"],
    "recommendation_map": ["guideline", "recommendation", "consensus", "statement"],
    "domain_map": ["domain_"],
    "protocol_rule": ["monitor", "safety", "dose", "follow-up"],
    "questionnaire_item_candidate": [
        "adherence",
        "behavior",
        "barrier",
        "facilitator",
        "self-monitor",
    ],
    "framework_component": ["framework", "competenc", "implementation", "pyramid"],
}

EVIDENCE_SIGNAL_RULES = [
    {
        "track": "guideline_map",
        "tier": "normative_high",
        "score": 14,
        "tokens": [
            "clinical practice guideline",
            "guideline",
            "guidelines",
            "food-based dietary guideline",
            "dietary guideline",
            "guideline for",
        ],
    },
    {
        "track": "guideline_map",
        "tier": "normative_high",
        "score": 13,
        "tokens": [
            "consensus",
            "scientific statement",
            "position statement",
            "recommendation",
            "recommendations",
        ],
    },
    {
        "track": "review_map",
        "tier": "synthesis_high",
        "score": 12,
        "tokens": [
            "umbrella review",
            "systematic review",
            "meta-analysis",
            "meta analysis",
            "evidence synthesis",
        ],
    },
    {
        "track": "review_map",
        "tier": "synthesis_support",
        "score": 9,
        "tokens": ["scoping review", "narrative review", "integrative review", "review"],
    },
    {
        "track": "intervention_map",
        "tier": "intervention_high",
        "score": 11,
        "tokens": [
            "randomized controlled trial",
            "randomised controlled trial",
            "randomized",
            "randomised",
            "controlled trial",
            "trial",
            "intervention",
        ],
    },
    {
        "track": "framework_map",
        "tier": "framework_high",
        "score": 11,
        "tokens": [
            "framework",
            "conceptual model",
            "logic model",
            "questionnaire",
            "instrument",
            "scale",
            "psychometric",
            "validation",
        ],
    },
    {
        "track": "implementation_map",
        "tier": "implementation_support",
        "score": 8,
        "tokens": [
            "implementation",
            "feasibility",
            "acceptability",
            "barrier",
            "facilitator",
            "adherence",
            "compliance",
        ],
    },
    {
        "track": "observational_map",
        "tier": "context_support",
        "score": 6,
        "tokens": [
            "cohort",
            "cross-sectional",
            "cross sectional",
            "observational",
            "registry",
        ],
    },
]

TRACK_USE_LABELS = {
    "guideline_map": "sustentação_recomendacao",
    "review_map": "síntese_evidência",
    "intervention_map": "efeito_intervenção",
    "framework_map": "construção_framework",
    "implementation_map": "implementação_adesão",
    "observational_map": "contexto_associativo",
    "background_map": "background_context",
}

QUESTIONNAIRE_COLUMNS = [
    "workstream",
    "documento_origem",
    "domínio",
    "termo_gatilho",
    "tipo_de_item",
    "formulação_sugerida",
    "justificativa_curta",
    "confiança",
    "translation_role",
]

FRAMEWORK_COLUMNS = [
    "componente",
    "workstream_origem",
    "domínio",
    "evidência_associada",
    "prioridade",
    "tipo",
    "observação",
]


def classify_nutev_objects(row: dict) -> list[str]:
    txt = f"{row.get('title', '')} {row.get('extracted_text', '')}".lower()
    out = []
    for obj, triggers in NUTEV_OBJECT_RULES.items():
        if any(tr in txt for tr in triggers):
            out.append(obj)
    return out or ["domain_map"]


def translation_potential(row: dict) -> str:
    objs = classify_nutev_objects(row)
    mapping = {
        "protocol_rule": "protocolo",
        "framework_component": "framework/piramide",
        "questionnaire_item_candidate": "item_questionario",
        "recommendation_map": "mapa_recomendacao",
        "evidence_table": "tabela_evidencia",
    }
    return ", ".join(mapping[o] for o in objs if o in mapping) or "mapa_dominio"


def _infer_evidence_profile(row: dict) -> dict[str, str | int]:
    title = (row.get("title") or "").lower()
    text = (row.get("extracted_text") or "").lower()
    doc_type = (row.get("doc_type") or "").lower()
    joined = f"{title} {doc_type} {text[:4000]}"

    best_track = "background_map"
    best_tier = "background"
    best_score = 3
    secondary_tracks: list[str] = []

    for rule in EVIDENCE_SIGNAL_RULES:
        if any(token in joined for token in rule["tokens"]):
            if rule["track"] not in secondary_tracks:
                secondary_tracks.append(rule["track"])
            if int(rule["score"]) > best_score:
                best_track = str(rule["track"])
                best_tier = str(rule["tier"])
                best_score = int(rule["score"])

    if best_track == "background_map":
        if doc_type == "guideline":
            best_track = "guideline_map"
            best_tier = "normative_high"
            best_score = 13
        elif doc_type == "study":
            best_track = "intervention_map"
            best_tier = "intervention_support"
            best_score = 7

    secondary = [
        TRACK_USE_LABELS[track]
        for track in secondary_tracks
        if track != best_track and track in TRACK_USE_LABELS
    ]
    primary_use = TRACK_USE_LABELS.get(best_track, "background_context")
    reading_lane = "support"
    if best_track in {"guideline_map", "review_map", "framework_map"}:
        reading_lane = "immediate"
    elif best_track in {"intervention_map", "implementation_map"}:
        reading_lane = "high"

    return {
        "evidence_priority_score": best_score,
        "evidence_priority_tier": best_tier,
        "evidence_use_track": best_track,
        "evidence_use_primary": primary_use,
        "evidence_use_secondary": ";".join(secondary),
        "reading_lane": reading_lane,
    }


def build_master_rows(rows: list[dict]) -> list[dict]:
    master = []
    for r in rows:
        text = r.get("extracted_text") or ""
        title = r.get("title") or ""
        domains = [
            k.replace("_present", "")
            for k, v in r.items()
            if k.endswith("_present") and v == 1
        ]
        patterns = infer_diet_pattern(f"{text} {title}")
        conds = infer_clinical_condition(f"{text} {title}")
        doc_type = r.get("doc_type", "unknown") if r.get("doc_type") else infer_doc_type(
            r.get("url", ""),
            title,
        )
        objs = classify_nutev_objects(r)
        evidence_profile = _infer_evidence_profile(
            {"title": title, "extracted_text": text, "doc_type": doc_type}
        )
        master.append(
            {
                "workstream": r.get("workstream", ""),
                "title": title,
                "source": normalize_source(r.get("source", "")),
                "url": r.get("url", ""),
                "file_path": r.get("file_path", ""),
                "year": r.get("year", "") or infer_year(f"{title} {text}"),
                "score": r.get("relevance_score", 0),
                "doc_type": doc_type,
                "domains": ";".join(domains),
                "main_terms": ";".join((patterns + conds)[:12]),
                "nutev_objects": ";".join(objs),
                "translation_potential": translation_potential(r),
                "ocr_status": r.get("ocr_status", "not_used"),
                "extraction_status": r.get("extraction_status", "unknown"),
                "diet_pattern": ";".join(patterns),
                "clinical_condition": ";".join(conds),
                "note": "auto_synth",
                "extracted_text_preview": text[:5000] if text else "",
                **evidence_profile,
            }
        )
    return master


def build_questionnaire_candidates(master_rows: list[dict]) -> list[dict]:
    focus = [
        "adherence",
        "behavior",
        "food literacy",
        "comensal",
        "culin",
        "planning",
        "self-monitor",
        "barrier",
        "facilitator",
        "implementation",
    ]
    items = []
    for r in master_rows:
        text = (
            f"{r.get('title', '')} {r.get('main_terms', '')} "
            f"{r.get('domains', '')} {r.get('evidence_use_primary', '')}"
        ).lower()
        for trig in focus:
            if trig in text:
                items.append(
                    {
                        "workstream": r["workstream"],
                        "documento_origem": r["title"],
                        "domínio": r.get("domains", ""),
                        "termo_gatilho": trig,
                        "tipo_de_item": "escala_likert",
                        "formulação_sugerida": f"Com que frequência você pratica {trig}?",
                        "justificativa_curta": "Derivado de termos recorrentes na evidência",
                        "confiança": "alta" if r.get("evidence_use_track") == "framework_map" else "media",
                        "translation_role": "questionnaire_item_candidate",
                    }
                )
    return items


def build_framework_components(master_rows: list[dict]) -> list[dict]:
    rows = []
    map_types = [
        ("ades", "base_comportamental"),
        ("diet", "recomendacao_alimentar"),
        ("compet", "competencia"),
        ("context", "contexto_ambiente"),
        ("monitor", "monitoramento"),
        ("safety", "seguranca"),
        ("implement", "implementacao"),
        ("framework", "implementacao"),
    ]
    for r in master_rows:
        low = (
            f"{r.get('title', '')} {r.get('domains', '')} {r.get('main_terms', '')} "
            f"{r.get('translation_potential', '')} {r.get('evidence_use_primary', '')}"
        ).lower()
        for key, typ in map_types:
            if key in low:
                rows.append(
                    {
                        "componente": key,
                        "workstream_origem": r["workstream"],
                        "domínio": r.get("domains", ""),
                        "evidência_associada": r["title"],
                        "prioridade": "alta"
                        if r.get("evidence_use_track") == "framework_map" or r.get("score", 0) >= 8
                        else "media",
                        "tipo": typ,
                        "observação": "gerado automaticamente",
                    }
                )
    return rows


def _count_by_split(df: pd.DataFrame, source_col: str, item_col: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[item_col, "n"])
    return (
        df.assign(**{item_col: df[source_col].fillna("").astype(str).str.split(";")})
        .explode(item_col)
        .assign(**{item_col: lambda x: x[item_col].astype(str).str.strip()})
        .query(f"{item_col} != ''")
        .groupby(item_col, dropna=False)
        .size()
        .reset_index(name="n")
        .sort_values(["n", item_col], ascending=[False, True])
    )


def write_synthesis_outputs(master_rows: list[dict], out_dir: Path) -> None:
    df = pd.DataFrame(master_rows)
    out_dir.mkdir(parents=True, exist_ok=True)

    if df.empty:
        df = pd.DataFrame(
            columns=[
                "workstream",
                "title",
                "source",
                "url",
                "file_path",
                "year",
                "score",
                "doc_type",
                "domains",
                "main_terms",
                "nutev_objects",
                "translation_potential",
                "ocr_status",
                "extraction_status",
                "diet_pattern",
                "clinical_condition",
                "note",
                "extracted_text_preview",
                "evidence_priority_score",
                "evidence_priority_tier",
                "evidence_use_track",
                "evidence_use_primary",
                "evidence_use_secondary",
                "reading_lane",
            ]
        )

    df["score"] = pd.to_numeric(df.get("score", 0), errors="coerce").fillna(0)
    df["evidence_priority_score"] = pd.to_numeric(
        df.get("evidence_priority_score", 0),
        errors="coerce",
    ).fillna(0)
    df["year_sort"] = pd.to_numeric(df.get("year", 0), errors="coerce").fillna(0)

    by_domain = _count_by_split(df, "domains", "domain")
    by_diet = _count_by_split(df, "diet_pattern", "diet")
    by_cond = _count_by_split(df, "clinical_condition", "cond")
    by_evidence_track = (
        df.groupby("evidence_use_track", dropna=False)
        .size()
        .reset_index(name="n")
        .sort_values(["n", "evidence_use_track"], ascending=[False, True])
    )
    by_evidence_tier = (
        df.groupby("evidence_priority_tier", dropna=False)
        .size()
        .reset_index(name="n")
        .sort_values(["n", "evidence_priority_tier"], ascending=[False, True])
    )

    top = df.sort_values(
        ["evidence_priority_score", "score", "year_sort", "title"],
        ascending=[False, False, False, True],
    ).drop(columns=["year_sort"]).head(200)

    evidence_sheets = {
        **{f"{ws}_documents": df[df["workstream"] == ws].drop(columns=["year_sort"]) for ws in ["busca1", "busca2a", "busca2b", "a3"]},
        "top_ranked": top,
        "by_source": df.groupby("source", dropna=False).size().reset_index(name="n"),
        "by_year": df.groupby("year", dropna=False).size().reset_index(name="n"),
        "by_domain": by_domain,
        "by_diet_pattern": by_diet,
        "by_clinical_condition": by_cond,
        "by_evidence_track": by_evidence_track,
        "by_evidence_tier": by_evidence_tier,
    }
    _write_workbook_or_csv(out_dir / "NUTEV_EVIDENCE_MASTER.xlsx", evidence_sheets)

    top.to_csv(out_dir / "NUTEV_TOP_DOCUMENTS.csv", index=False)
    write_excel_file(top, out_dir / "NUTEV_TOP_DOCUMENTS.xlsx")
    write_excel_file(
        df.groupby("source", dropna=False).size().reset_index(name="n"),
        out_dir / "NUTEV_SOURCE_SUMMARY.xlsx",
    )
    write_excel_file(by_domain, out_dir / "NUTEV_DOMAIN_SUMMARY.xlsx")

    map_sheets = {}
    for track in [
        "guideline_map",
        "review_map",
        "intervention_map",
        "framework_map",
        "implementation_map",
        "observational_map",
    ]:
        map_sheets[track] = df[df["evidence_use_track"] == track].sort_values(
            ["evidence_priority_score", "score", "year_sort", "title"],
            ascending=[False, False, False, True],
        ).drop(columns=["year_sort"])
    map_sheets["summary"] = by_evidence_track
    _write_workbook_or_csv(out_dir / "NUTEV_ARTICLE_EVIDENCE_MAP.xlsx", map_sheets)

    questionnaire_df = pd.DataFrame(
        build_questionnaire_candidates(master_rows),
        columns=QUESTIONNAIRE_COLUMNS,
    )
    framework_df = pd.DataFrame(
        build_framework_components(master_rows),
        columns=FRAMEWORK_COLUMNS,
    )
    write_excel_file(questionnaire_df, out_dir / "NUTEV_QUESTIONNAIRE_ITEM_CANDIDATES.xlsx")
    write_excel_file(framework_df, out_dir / "NUTEV_FRAMEWORK_COMPONENTS.xlsx")
