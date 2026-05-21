# NutEV Evidence → Protocol Flow

Este fluxo operacionaliza a cadeia de rastreabilidade:

1. **EvidenceRecord** (metadata master integrado)
2. **EvidenceClaim** (frase/citação com domínio, status e vínculo documental)
3. **ClaimEvaluation** (avaliação rule-based e sinalização de revisão humana)
4. **RecommendationCandidate** (somente candidata; sem aprovação automática)
5. **HumanReviewQueue** (claims/recomendações pendentes de validação humana)
6. **GlobalEvidenceMatrix** (visão integrada multi-lentes)
7. **ProtocolTranslationMatrix** (tradução para componentes do protocolo)

## Regras críticas
- Nenhuma recomendação em `ready_for_human_review`/`approved_for_protocol` pode existir sem `supporting_claim_ids`.
- Claims sem `exact_quote` devem ir para revisão humana.
- Claims `inference_only` não sustentam aprovação final automática.
- Conflitos de evidência são preservados em matriz de conflito.

## Outputs para qualificação
No `project_output/06_tables`:
- `NUTEV_EVIDENCE_CLAIMS.xlsx`
- `NUTEV_RECOMMENDATION_CANDIDATES.xlsx`
- `NUTEV_HUMAN_REVIEW_QUEUE.xlsx`
- `NUTEV_CONFLICTING_EVIDENCE.xlsx`
- `NUTEV_GLOBAL_EVIDENCE_MATRIX.xlsx`
- `NUTEV_PROTOCOL_TRANSLATION_MATRIX.xlsx`

No `project_output/02_metadata`:
- CSVs equivalentes para auditoria e reprocessamento.

## Teste end-to-end recomendado
```bash
PYTHONPATH=src python -m pytest -q tests/nutev/test_pipeline_audit_integration.py
```

## Revisão humana e decisão final
Use `human_review_decisions.csv` para registrar decisões de revisores. Sem `final_decision=approved`, não há aprovação final.
