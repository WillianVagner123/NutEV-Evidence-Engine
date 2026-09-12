# Documentação do NutEV Reference Engine

Esta pasta contém a documentação **corrente** do produto suportado. Relatórios de sprint, dry-runs, smoke reports e closeouts históricos ficam em [`archive/`](archive/) para não competir com os contratos vivos do sistema.

## Identidade atual

```text
version = 1.1.0
tag = v1.1.0
immutable_release_sha = 49588233ad2828b8fcc6140398ab55aedf7c03ef
GitHub Release = published
Zenodo record = 22726717
DOI = 10.5281/zenodo.22726717
production = accepted
scientific verdict = B — DEMOTE
```

Software publicado/arquivado e validade científica são gates diferentes.

## Comece por aqui

1. [`POP_USO_NUTEV_REFERENCE_ENGINE.md`](POP_USO_NUTEV_REFERENCE_ENGINE.md) — instalação/execução Windows, outputs, auditoria e recuperação.
2. [`ARCHITECTURE.md`](ARCHITECTURE.md) — arquitetura do pipeline e contratos de dados.
3. [`TAXONOMY.md`](TAXONOMY.md) — taxonomia canônica e governança de termos.
4. [`AUDITABILITY_AND_GUARDRAILS.md`](AUDITABILITY_AND_GUARDRAILS.md) — hashes, rastreabilidade, quarentena e fail-closed.
5. [`SEARCH_PROVIDERS.md`](SEARCH_PROVIDERS.md) — providers, credenciais e estados de indisponibilidade.
6. [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md) — limites de interpretação e validação.
7. [`PRODUCTION_USABILITY_AUDIT.md`](PRODUCTION_USABILITY_AUDIT.md) — estado atual da auditoria de produto/UX.
8. [`../validation/SCIENTIFIC_VALIDATION_STATUS.md`](../validation/SCIENTIFIC_VALIDATION_STATUS.md) — estado científico e freeze histórico de validação.

## Produto hospedado e multi-tenant

- [`MULTITENANT_APPLICATION_LAYER.md`](MULTITENANT_APPLICATION_LAYER.md) — ResearchApplications reutilizáveis e escopo por projeto.
- [`MULTITENANT_AUTH_SESSION.md`](MULTITENANT_AUTH_SESSION.md) — identidade/sessão e fronteira de autenticação.
- [`MULTITENANT_WORKSPACE_PROJECT_ACCESS.md`](MULTITENANT_WORKSPACE_PROJECT_ACCESS.md) — autorização por workspace/projeto.
- [`FINAL_MULTITENANT_RELEASE_GATE.md`](FINAL_MULTITENANT_RELEASE_GATE.md) — barreira de promoção do runtime multi-tenant.
- [`archive/2026/PRODUCT_DEATH_TEST_REPORT.md`](archive/2026/PRODUCT_DEATH_TEST_REPORT.md) — relatório **histórico** do death test de 10/09/2026; não é o estado atual de produção.
- [`../apps/nutev-web/README.md`](../apps/nutev-web/README.md) — diferença entre runtime hospedado e servidor científico/local.

A jornada genérica suportada é:

```text
LOGIN -> WORKSPACE -> PROJECT -> RESEARCH APPLICATION -> SEARCH -> LIBRARY -> EXPORT
```

Review/síntese/metodologia especializada entram quando a ResearchApplication e a superfície correspondente suportam aquele fluxo. Rotas específicas de Article 1 não devem ser promovidas como recursos genéricos de todos os projetos.

## Workspace científico e síntese

Documentos vivos de capacidades científicas especializadas permanecem no nível principal, entre eles:

- [`QUALITY_OBSERVATORY.md`](QUALITY_OBSERVATORY.md)
- [`SCIENTIFIC_INTELLIGENCE.md`](SCIENTIFIC_INTELLIGENCE.md)
- [`HUMAN_SYNTHESIS_REVIEW.md`](HUMAN_SYNTHESIS_REVIEW.md)
- [`HUMAN_SYNTHESIS_BRIEF.md`](HUMAN_SYNTHESIS_BRIEF.md)
- [`SYNTHESIS_GOVERNANCE_REGISTRY.md`](SYNTHESIS_GOVERNANCE_REGISTRY.md)
- [`GOVERNED_SYNTHESIS_RELEASE.md`](GOVERNED_SYNTHESIS_RELEASE.md)
- [`GOVERNED_PUBLICATION_MANIFEST.md`](GOVERNED_PUBLICATION_MANIFEST.md)
- [`EVIDENCE_CLAIM_REVIEW.md`](EVIDENCE_CLAIM_REVIEW.md)
- [`CLAIM_EVALUATION_APPRAISAL.md`](CLAIM_EVALUATION_APPRAISAL.md)
- [`EVIDENCE_SET_CONSTRUCTION.md`](EVIDENCE_SET_CONSTRUCTION.md)
- [`RECOMMENDATION_CANDIDATE_DRAFTING.md`](RECOMMENDATION_CANDIDATE_DRAFTING.md)
- [`RECOMMENDATION_HUMAN_VALIDATION.md`](RECOMMENDATION_HUMAN_VALIDATION.md)
- [`RECOMMENDATION_DEVELOPMENT.md`](RECOMMENDATION_DEVELOPMENT.md)

Essas superfícies registram estados/decisões humanas e proveniência. Nenhuma delas transforma integridade de software em certeza científica, decisão clínica ou recomendação automática.

## Release, DOI e proveniência

- [`RELEASE_NOTES_1_1_0.md`](RELEASE_NOTES_1_1_0.md) — release estável atual.
- [`RELEASE_V1_0_0.md`](RELEASE_V1_0_0.md) — release histórica anterior.
- [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md) — checklist de futuras releases.
- [`ZENODO_SETUP.md`](ZENODO_SETUP.md) — integração GitHub/Zenodo e regra de DOI.
- [`PROVENANCE_AND_LICENSE.md`](PROVENANCE_AND_LICENSE.md) — proveniência e licença.
- [`PUBLICATION_READINESS.md`](PUBLICATION_READINESS.md) — fechamento de publicação 1.1.0.
- [`FINAL_SYSTEM_ACCEPTANCE.md`](FINAL_SYSTEM_ACCEPTANCE.md) — aceite final do software.
- [`SYSTEM_CLOSEOUT_MASTER.md`](SYSTEM_CLOSEOUT_MASTER.md) — ledger de fechamento do sistema.

## Referência operacional

Fluxo do Reference Engine:

```text
SEARCH -> NORMALIZE -> DEDUPLICATE -> TRACEABILITY GATE -> RANK -> EXPORT -> AUDIT
```

Entrada Windows suportada:

```text
Iniciar-NutEV-Windows.bat
```

Saídas de ranking/auditoria ficam em `project_output_reference/` e não devem ser tratadas como documentação versionada do produto.

## Arquivo histórico

Use [`archive/README.md`](archive/README.md) para localizar evidência histórica de sprints, migrações e homologações anteriores.

Regra editorial:

- **documento vivo**: descreve o produto atualmente suportado;
- **arquivo histórico**: descreve um estado passado e não governa a `main` atual;
- **transitório supersedido**: é removido do working tree; o Git continua preservando seu histórico.

A execução Windows validada em 18/08/2026, por exemplo, permanece preservada em [`archive/2026/VALIDATED_WINDOWS_RUN_2026-08-18.md`](archive/2026/VALIDATED_WINDOWS_RUN_2026-08-18.md), mas não é baseline obrigatório da versão 1.1.0.