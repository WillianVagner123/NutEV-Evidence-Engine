from __future__ import annotations

import json
from pathlib import Path

from nutev.utils import write_text


def _load_provider_querypack(logs_dir: Path) -> dict[str, dict[str, list[str]]]:
    querypack_path = logs_dir / "provider_querypack_executed.json"
    if not querypack_path.exists():
        return {}
    return json.loads(querypack_path.read_text(encoding="utf-8"))


def _provider_section(
    workstream: str,
    provider_querypack: dict[str, dict[str, list[str]]],
) -> str:
    providers = provider_querypack.get(workstream, {})
    if not providers:
        return "## estratégia por base\nNão disponível para esta rodada.\n"

    lines = ["## estratégia por base"]
    for provider, queries in providers.items():
        lines.append(f"### {provider}")
        if not queries:
            lines.append("Nenhuma query executada.")
            continue
        for idx, query in enumerate(queries[:5], start=1):
            lines.append(f"{idx}. {query}")
    return "\n".join(lines) + "\n"


def _method_doc(
    workstream: str,
    provider_querypack: dict[str, dict[str, list[str]]],
) -> str:
    return f"""# NUTEV METHODS - {workstream.upper()}

## objetivo
Executar captura reprodutível de evidências para {workstream}.

## fontes consultadas
PubMed, Europe PMC, OpenAlex, Crossref e fontes oficiais do manifest.

## lógica metodológica
A estratégia é derivada de `config/keyword_taxonomy.json`, mas a execução final usa renderização específica por base para reduzir fragilidade e melhorar auditabilidade.

## camada global de evidência NutEV (integrada)
A classificação não funciona mais como silos isolados por workstream. Os fluxos `busca1`, `busca2a`, `busca2b` e `a3` são tratados como **lentes de evidência** sobre a mesma base de registros:
- `config/nutev_ontology.json`: ontologia central (domínios, outcomes, tipos de evidência).
- `config/evidence_lenses.json`: mapeamento das lentes e regras multi-rótulo.
- `config/source_registry.json`: registro de provedores/fontes e compatibilidade.
- `src/nutev/analysis/nutev_classifier.py`: classificador unificado aplicado em todos os registros, independentemente do workstream de origem.

Saídas integradas:
- `NUTEV_GLOBAL_EVIDENCE_MATRIX.xlsx`
- `NUTEV_PROTOCOL_TRANSLATION_MATRIX.xlsx`

## Auditoria, rastreabilidade e controle de inferências
“A etapa de auditoria foi planejada para reduzir o risco de inferências não rastreáveis. Cada recomendação candidata do Protocolo NutEV deverá estar vinculada a um ou mais EvidenceClaims, e cada EvidenceClaim deverá estar vinculado a um documento identificado no Metadata Master. A pré-codificação computacional será utilizada para organização e geração de candidatos à síntese, mas não substituirá a triagem, interpretação e validação por revisores humanos. Recomendações sem claims documentais suficientes serão classificadas como draft_needs_evidence ou insufficient_evidence, e não como diretrizes finais.”

“Claims classificados como inference_only não poderão sustentar recomendações finais sem validação humana.”

“Conflitos entre documentos ou recomendações serão preservados em matriz específica de evidências conflitantes, sem exclusão automática.”

{_provider_section(workstream, provider_querypack)}## auditoria da busca
As queries efetivamente executadas ficam registradas em `07_logs/querypack_executed.json`, `07_logs/querypack_executed.csv`, `07_logs/provider_querypack_executed.json` e `07_logs/provider_querypack_executed.csv`.

## critérios de captura
Resultados dos providers suportados mais manifest oficial.

## critérios de download
Seleção por relevância, regras de domínio e orçamento operacional, com preservação explícita de falhas em `failed_downloads.csv`.

## lógica de OCR
PDF: texto nativo primeiro; sem texto, OCR por página. Imagens: OCR direto.

## regras de scoring
Scoring por keyword, source e workstream via `config/scoring_rules.json`.

## análise por domínios
Regras `domain_rules_{workstream}.json` quando aplicável.

## outputs gerados
Tabelas 02_metadata, 05_extraction, 06_tables, 10_curated e logs 07_logs.

## limitações reais
Ainda é uma estratégia operacional reprodutível e auditável. Para submissão de artigo, a seção de métodos deve explicitar também data da busca, critérios de inclusão/exclusão e justificativa de bases.
"""


def write_methods_docs(docs_dir: Path, logs_dir: Path | None = None) -> None:
    provider_querypack = {}
    if logs_dir is not None:
        provider_querypack = _load_provider_querypack(logs_dir)

    workstreams = ["busca1", "busca2a", "busca2b", "a3"]
    for ws in workstreams:
        write_text(
            docs_dir / f"NUTEV_METHODS_{ws.upper()}.md",
            _method_doc(ws, provider_querypack),
        )
    write_text(
        docs_dir / "NUTEV_METHODS_MASTER.md",
        "\n\n".join(_method_doc(ws, provider_querypack) for ws in workstreams),
    )
