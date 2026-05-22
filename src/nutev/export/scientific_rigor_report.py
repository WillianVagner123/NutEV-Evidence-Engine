from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_TEXT = (
    "A entrada de uma recomendacao no Protocolo NutEV requer lastro documental, "
    "claim auditavel, avaliacao de qualidade da evidencia, ausencia de conflito nao "
    "adjudicado e validacao humana. Recomendacoes candidatas sem suporte documental "
    "suficiente serao classificadas como lacunas ou itens pendentes de revisao, nao "
    "como diretrizes finais."
)


def _count(obj: Any) -> int:
    if obj is None:
        return 0
    try:
        return len(obj)
    except Exception:
        return 0


def write_scientific_rigor_report(
    docs_dir: Path,
    conceptual_model: dict[str, Any] | None = None,
    claims: list[Any] | None = None,
    recommendations: list[Any] | None = None,
    conflicts: list[dict[str, Any]] | None = None,
    convergence_summary: dict[str, int] | None = None,
    protocol_ready_total: int = 0,
    evidence_gaps_total: int = 0,
    locked_protocol_items_total: int = 0,
) -> Path:
    docs_dir.mkdir(parents=True, exist_ok=True)
    conceptual_model = conceptual_model or {}
    convergence_summary = convergence_summary or {}
    lines = [
        "# NUTEV SCIENTIFIC RIGOR REPORT",
        "",
        "## 1. Modelo conceitual NutEV",
        conceptual_model.get("definition_pt", "Modelo conceitual nao disponivel."),
        "",
        "## 2. Originalidade e contribuicao",
        conceptual_model.get("originality_claim", "Originalidade nao documentada."),
        "",
        "## 3. Qualidade da evidencia",
        "Claims e recomendacoes candidatas sao classificados por tipo de evidencia, suporte documental e necessidade de revisao humana.",
        "",
        "## 4. Convergencia de evidencias",
        f"Tabelas de convergencia geradas: {json.dumps(convergence_summary, ensure_ascii=False)}",
        "",
        "## 5. Revisao humana, dupla revisao e adjudicacao",
        "Itens sem suporte, com inferencia computacional ou conflito permanecem pendentes de revisao humana/adjudicacao.",
        "",
        "## 6. Protocol readiness",
        f"Itens protocol_ready: {protocol_ready_total}",
        "",
        "## 7. Lacunas de evidencia",
        f"Lacunas registradas: {evidence_gaps_total}",
        "",
        "## 8. Itens bloqueados ou pendentes",
        f"Itens bloqueados/locked para protocolo: {locked_protocol_items_total}",
        "",
        "## 9. Papel permitido do LLM",
        "LLM e assistivo apenas. LLM nao aprova recomendacoes finais, nao substitui revisor humano e nao cria suporte documental sem documento/claim.",
        "",
        "## 10. Criterios para recomendacao entrar no protocolo",
        REQUIRED_TEXT,
        "",
        "## 11. Metricas resumidas",
        f"Claims: {_count(claims)}",
        f"RecommendationCandidates: {_count(recommendations)}",
        f"Conflitos: {_count(conflicts)}",
        "",
        "## 12. Proximos passos",
        "Revisar lacunas, executar dupla revisao humana, adjudicar conflitos e rodar piloto real com documentos selecionados.",
    ]
    path = docs_dir / "NUTEV_SCIENTIFIC_RIGOR_REPORT.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_originality_matrix(config_root: Path, tables_dir: Path) -> int:
    rows = [
        {"existing_field": "Food-based dietary guidelines", "what_exists": "Population guidance", "limitation": "Limited clinical-behavioral translation", "nutev_contribution": "Translates dietary guidance into protocol components", "protocol_component": "diretrizes_dieteticas", "evidence_lens": "official_guidelines", "notes": ""},
        {"existing_field": "Clinical nutrition guidelines", "what_exists": "Condition-specific recommendations", "limitation": "Often siloed by disease", "nutev_contribution": "Integrates clinical modifiers into Lifestyle Nutrition", "protocol_component": "modificadores_clinicos", "evidence_lens": "clinical_guidelines", "notes": ""},
        {"existing_field": "Lifestyle Medicine", "what_exists": "Pillars and broad principles", "limitation": "Nutrition pillar may lack detailed protocol", "nutev_contribution": "Operationalizes the nutrition pillar", "protocol_component": "protocolo_nutev", "evidence_lens": "lifestyle_medicine", "notes": ""},
        {"existing_field": "Dietary patterns", "what_exists": "MED, DASH, plant-based and other patterns", "limitation": "Pattern evidence not unified for implementation", "nutev_contribution": "Maps patterns to protocol components", "protocol_component": "padroes_dieteticos", "evidence_lens": "dietary_patterns", "notes": ""},
        {"existing_field": "Behavioral nutrition", "what_exists": "Behavior change strategies", "limitation": "Often separated from dietary protocol", "nutev_contribution": "Links adherence and competence to protocol readiness", "protocol_component": "adesao_implementacao", "evidence_lens": "behavior", "notes": ""},
        {"existing_field": "Culinary medicine", "what_exists": "Cooking skills interventions", "limitation": "Variable integration with clinical dietetics", "nutev_contribution": "Includes culinary skills as protocol competencies", "protocol_component": "competencias_alimentares", "evidence_lens": "implementation", "notes": ""},
        {"existing_field": "Food literacy", "what_exists": "Knowledge/skills frameworks", "limitation": "Not always connected to clinical outcomes", "nutev_contribution": "Links literacy to adherence and implementation", "protocol_component": "food_literacy", "evidence_lens": "implementation", "notes": ""},
        {"existing_field": "Implementation science", "what_exists": "Implementation frameworks", "limitation": "Rarely embedded in diet protocol outputs", "nutev_contribution": "Adds review queue, readiness and gap register", "protocol_component": "protocol_readiness", "evidence_lens": "implementation", "notes": ""},
        {"existing_field": "Obesity/cardiometabolic care", "what_exists": "Clinical risk management", "limitation": "Multiple comorbidity-specific documents", "nutev_contribution": "Unifies cardiometabolic modifiers", "protocol_component": "modificadores_clinicos", "evidence_lens": "clinical", "notes": ""},
        {"existing_field": "Planetary health/sustainable diets", "what_exists": "Sustainable diet principles", "limitation": "May not be clinically translated", "nutev_contribution": "Allows sustainability as contextual lens", "protocol_component": "diretrizes_dieteticas", "evidence_lens": "sustainability", "notes": ""},
    ]
    df = pd.DataFrame(rows)
    from nutev.export.excel_writer import write_excel_file
    write_excel_file(df, tables_dir / "NUTEV_ORIGINALITY_MATRIX.xlsx")
    return len(df)
