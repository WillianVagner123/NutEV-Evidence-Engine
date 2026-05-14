from __future__ import annotations

from collections import Counter
from pathlib import Path
import pandas as pd
from nutev.search.normalize import infer_year, infer_doc_type, infer_diet_pattern, infer_clinical_condition, normalize_source

DIET_PATTERNS = ["mediterranean", "dash", "keto", "ketogenic", "vegetarian", "vegan", "plant-based", "low-carb"]
CLINICAL_CONDITIONS = ["diabetes", "hypertension", "dyslipidemia", "cardiovascular", "metabolic syndrome", "nafld", "masld"]
NUTEV_OBJECT_RULES = {
    "evidence_table": ["trial", "meta", "review", "cohort"],
    "recommendation_map": ["guideline", "recommendation", "consensus", "statement"],
    "domain_map": ["domain_"],
    "protocol_rule": ["monitor", "safety", "dose", "follow-up"],
    "questionnaire_item_candidate": ["adherence", "behavior", "barrier", "facilitator", "self-monitor"],
    "framework_component": ["framework", "competenc", "implementation", "pyramid"],
}


def _detect_terms(text: str, terms: list[str]) -> list[str]:
    t = (text or "").lower()
    return [x for x in terms if x in t]


def classify_nutev_objects(row: dict) -> list[str]:
    txt = f"{row.get('title','')} {row.get('extracted_text','')}".lower()
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


def build_master_rows(rows: list[dict]) -> list[dict]:
    master = []
    for r in rows:
        text = (r.get("extracted_text") or "")
        domains = [k.replace("_present", "") for k, v in r.items() if k.endswith("_present") and v == 1]
        patterns = infer_diet_pattern(text + " " + (r.get("title") or ""))
        conds = infer_clinical_condition(text + " " + (r.get("title") or ""))
        objs = classify_nutev_objects(r)
        master.append({
            "workstream": r.get("workstream", ""), "title": r.get("title", ""), "source": normalize_source(r.get("source", "")), "url": r.get("url", ""),
            "file_path": r.get("file_path", ""), "year": r.get("year", "") or infer_year((r.get("title","")+" "+text)), "score": r.get("relevance_score", 0),
            "doc_type": r.get("doc_type", "unknown") if r.get("doc_type") else infer_doc_type(r.get("url",""), r.get("title","")), "domains": ";".join(domains), "main_terms": ";".join((patterns + conds)[:12]),
            "nutev_objects": ";".join(objs), "translation_potential": translation_potential(r),
            "ocr_status": r.get("ocr_status", "not_used"), "extraction_status": r.get("extraction_status", "unknown"),
            "diet_pattern": ";".join(patterns), "clinical_condition": ";".join(conds), "note": "auto_synth",
        })
    return master


def build_questionnaire_candidates(master_rows: list[dict]) -> list[dict]:
    focus = ["adherence", "behavior", "food literacy", "comensal", "culin", "planning", "self-monitor", "barrier", "facilitator", "implementation"]
    items = []
    for r in master_rows:
        text = f"{r.get('title','')} {r.get('main_terms','')} {r.get('domains','')}".lower()
        for trig in focus:
            if trig in text:
                items.append({
                    "workstream": r["workstream"], "documento_origem": r["title"], "domínio": r.get("domains", ""), "termo_gatilho": trig,
                    "tipo_de_item": "escala_likert", "formulação_sugerida": f"Com que frequência você pratica {trig}?",
                    "justificativa_curta": "Derivado de termos recorrentes na evidência", "confiança": "media", "translation_role": "questionnaire_item_candidate",
                })
    return items


def build_framework_components(master_rows: list[dict]) -> list[dict]:
    rows = []
    map_types = [("ades", "base_comportamental"), ("diet", "recomendacao_alimentar"), ("compet", "competencia"), ("context", "contexto_ambiente"), ("monitor", "monitoramento"), ("safety", "seguranca"), ("implement", "implementacao"), ("framework", "implementacao")]
    for r in master_rows:
        low = f"{r.get('title','')} {r.get('domains','')} {r.get('main_terms','')} {r.get('translation_potential','')}".lower()
        for key, typ in map_types:
            if key in low:
                rows.append({"componente": key, "workstream_origem": r["workstream"], "domínio": r.get("domains",""), "evidência_associada": r["title"], "prioridade": "alta" if r.get("score",0) >= 8 else "media", "tipo": typ, "observação": "gerado automaticamente"})
    return rows


def write_synthesis_outputs(master_rows: list[dict], out_dir: Path) -> None:
    df = pd.DataFrame(master_rows)
    out_dir.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_dir / "NUTEV_EVIDENCE_MASTER.xlsx") as w:
        for ws in ["busca1", "busca2a", "busca2b", "a3"]:
            df[df["workstream"] == ws].to_excel(w, sheet_name=f"{ws}_documents", index=False)
        df.sort_values("score", ascending=False).head(200).to_excel(w, sheet_name="top_ranked", index=False)
        df.groupby("source", dropna=False).size().reset_index(name="n").to_excel(w, sheet_name="by_source", index=False)
        df.groupby("year", dropna=False).size().reset_index(name="n").to_excel(w, sheet_name="by_year", index=False)
        df.assign(domain=df["domains"].fillna("").str.split(";")).explode("domain").groupby("domain", dropna=False).size().reset_index(name="n").to_excel(w, sheet_name="by_domain", index=False)
        df.assign(diet=df["diet_pattern"].fillna("").str.split(";")).explode("diet").groupby("diet", dropna=False).size().reset_index(name="n").to_excel(w, sheet_name="by_diet_pattern", index=False)
        df.assign(cond=df["clinical_condition"].fillna("").str.split(";")).explode("cond").groupby("cond", dropna=False).size().reset_index(name="n").to_excel(w, sheet_name="by_clinical_condition", index=False)
    top = df.sort_values("score", ascending=False).head(200)
    top.to_csv(out_dir / "NUTEV_TOP_DOCUMENTS.csv", index=False)
    top.to_excel(out_dir / "NUTEV_TOP_DOCUMENTS.xlsx", index=False)
    df.groupby("source", dropna=False).size().reset_index(name="n").to_excel(out_dir / "NUTEV_SOURCE_SUMMARY.xlsx", index=False)
    df.assign(domain=df["domains"].fillna("").str.split(";")).explode("domain").groupby("domain", dropna=False).size().reset_index(name="n").to_excel(out_dir / "NUTEV_DOMAIN_SUMMARY.xlsx", index=False)
