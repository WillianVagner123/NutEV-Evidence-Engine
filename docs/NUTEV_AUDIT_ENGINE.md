# NutEV Audit Engine

## 1. O que é
Camada anti-alucinação para rastrear documento → claim → recomendação candidata.
## 2. Por que existe
Evitar recomendações finais sem lastro documental explícito.
## 3. Como reduz alucinação
Bloqueia aprovação automática e exige claims/documentos vinculados.
## 4. Diferença entre entidades
- EvidenceRecord: registro bruto integrado.
- EvidenceClaim: afirmação extraída/normalizada com citação e status.
- RecommendationCandidate: proposta ligada a claims de suporte.
## 5. Extração de claims
Determinística por regras léxicas usando title/abstract/extracted_text.
## 6. Avaliação de claims
Rule-based com validação de quote, tipo de evidência e status.
## 7. Geração de recomendações candidatas
Somente com supporting_claim_ids e sem aprovação final automática.
## 8. O que exige validação humana
Claims inference_only, sem quote, conflitos e toda aprovação final.
## 9. Interpretação de status
Use claim_status/recommendation_status/human_validation_status.
## 10. Uso na qualificação
Matrizes de claims, conflitos e fila humana sustentam revisão.
## 11. Limitações
Sem NLP semântico avançado/LLM nesta fase inicial.
## 12. Próximos passos
Calibração de regras, revisão dupla e integração com UI de curadoria.
