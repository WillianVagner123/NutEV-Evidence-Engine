# NutEV Pilot Real Protocol (20–30 documentos)

## Objetivo
Executar um primeiro piloto real para validar operacionalmente a cadeia EvidenceRecord → EvidenceClaim → RecommendationCandidate com revisão humana.

## Escopo
- 20–30 documentos.
- Workstreams: busca1, busca2a, busca2b, a3.
- Priorizar: guias alimentares, diretrizes clínicas, revisões sistemáticas/umbrella e intervenções.

## Comandos sugeridos
```bash
nutev --project-root ./project_output_pilot --workstreams busca1 busca2a busca2b a3 --web-enabled
nutev pilot-report --project-root ./project_output_pilot
nutev dashboard --project-root ./project_output_pilot --port 8501
```

## Critérios de seleção
- Relevância direta para NutEV.
- Preferência para evidência normativa/síntese de alta qualidade.
- Representação dos quatro workstreams.

## Checklist de curadoria humana
Usar `docs/NUTEV_HUMAN_CURATION_CHECKLIST.md`.

## Outputs esperados
- `02_metadata/metadata_master.csv`
- `02_metadata/NUTEV_EVIDENCE_CLAIMS.csv`
- `02_metadata/NUTEV_RECOMMENDATION_CANDIDATES.csv`
- `06_tables/NUTEV_GLOBAL_EVIDENCE_MATRIX.xlsx`
- `06_tables/NUTEV_PROTOCOL_TRANSLATION_MATRIX.xlsx`
- `06_tables/NUTEV_HUMAN_REVIEW_QUEUE.xlsx`
- `08_docs/NUTEV_PILOT_REPORT.md`

## Critérios de sucesso
- Claims com quote_location consistente.
- Recomendações candidatas com supporting_claim_ids quando aplicável.
- Conflitos e insuficiência de evidência explicitamente registrados.
- Revisão humana registrada em `07_logs/human_review_decisions.csv`.

## Limitações
- Piloto não substitui revisão sistemática final.
- Dependência de disponibilidade de fontes na web.

## Como transformar em qualificação
Converter matriz + fila de revisão + relatório piloto em seção de método, resultados preliminares e lacunas priorizadas.
