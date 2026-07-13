from __future__ import annotations

from nutev.querypacks import semantic_blocks

IBEROAMERICAN_FOOD_GUIDANCE_TERMS = [
    "guia alimentar",
    "guias alimentares",
    "guia alimentar para a populacao brasileira",
    "guia alimentar para a população brasileira",
    "guia alimentar brasileiro",
    "guias alimentares baseados em alimentos",
    "diretrizes alimentares",
    "recomendacoes alimentares",
    "recomendações alimentares",
    "orientacao alimentar",
    "orientação alimentar",
    "alimentacao adequada e saudavel",
    "alimentação adequada e saudável",
    "educacao alimentar e nutricional",
    "educação alimentar e nutricional",
    "guia alimentaria",
    "guia alimentario",
    "guias alimentarias",
    "guías alimentarias",
    "guias alimentarias basadas en alimentos",
    "guías alimentarias basadas en alimentos",
    "guia alimentaria para la poblacion",
    "guía alimentaria para la población",
    "recomendaciones alimentarias",
    "orientacion alimentaria",
    "orientación alimentaria",
    "alimentacion saludable",
    "alimentación saludable",
    "educacion alimentaria y nutricional",
    "educación alimentaria y nutricional",
    "ambiente alimentar",
    "ambiente alimentario",
    "comensalidade",
    "comensalidad",
    "refeicoes compartilhadas",
    "refeições compartilhadas",
    "comer junto",
]

IBEROAMERICAN_FOOD_GUIDANCE_DOCUMENT_TERMS = [
    "guia alimentar para a populacao brasileira",
    "guia alimentar para a população brasileira",
    "guias alimentares baseados em alimentos",
    "diretrizes alimentares",
    "recomendacoes alimentares",
    "recomendações alimentares",
    "guia alimentaria para la poblacion",
    "guía alimentaria para la población",
    "guias alimentarias basadas en alimentos",
    "guías alimentarias basadas en alimentos",
    "recomendaciones alimentarias",
    "educacao alimentar e nutricional",
    "educación alimentaria y nutricional",
]


def _extend_unique(existing: list[str], additions: list[str]) -> list[str]:
    seen = {item.lower() for item in existing}
    for item in additions:
        value = item.strip()
        if not value or value.lower() in seen:
            continue
        existing.append(value)
        seen.add(value.lower())
    return existing


def _extend_semantic_block(
    block_name: str,
    *,
    terms: list[str],
    document_terms: list[str],
) -> None:
    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS.setdefault(
        block_name,
        {"terms": [], "document_terms": []},
    )
    block["terms"] = _extend_unique(block.setdefault("terms", []), terms)
    block["document_terms"] = _extend_unique(
        block.setdefault("document_terms", []),
        document_terms,
    )


def apply_iberoamerican_guidance_extensions() -> None:
    for block_name in (
        "evidence_synthesis",
        "food_literacy_agency",
        "commensality_context",
        "lifestyle_nutrition_patterns",
    ):
        _extend_semantic_block(
            block_name,
            terms=IBEROAMERICAN_FOOD_GUIDANCE_TERMS,
            document_terms=IBEROAMERICAN_FOOD_GUIDANCE_DOCUMENT_TERMS,
        )
