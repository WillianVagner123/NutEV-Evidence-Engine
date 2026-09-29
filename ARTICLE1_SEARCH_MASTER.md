# Article 1 — Search Master

**Canonical status:** `PRESS_COMPLETE_GF10_PENDING`

This is the main human-readable control file for the Article 1 search. For machine-readable state use `config/nutev/article1_search_master_v1.json`. For AI/agent access start at `AI_CONTEXT.md`.

## Research question

> Como documentos normativos e estruturantes do cuidado alimentar de adultos formulam recomendações e direção dietética e em que medida as operacionalizam por meio de formas de prescrição, competências e repertórios, contexto, condições de execução, monitoramento e continuidade do cuidado?

**Decision:** approved by Willian Vagner and supervisor Prof. Dr. Caio Eduardo G. Reis on 2026-09-28. This resolves the prior manuscript/protocol/Engine question drift. It does **not** itself approve PRESS, GF-10, query freeze or formal search.

## What is already closed

The broad discovery/harvest stage is technically complete and persisted under search id:

`web_20260830T182743+0000_91bde5be`

Production snapshot verified by the operator on 2026-08-30:

- 41,139 records before deduplication;
- 33,839 unique references in the discovery corpus;
- 33,067 structurally accepted records and 772 structurally quarantined records;
- Tier A: 662/662 documents deepened;
- Tier A retrieval: 504 `retrieved`, 90 `partial`, 68 `not_retrieved`;
- 594/662 (89.73%) retrieved or partially retrieved;
- deepening integrity audit: PASS, 27 v3 batches, 662 rank coverage, 459 SHA-256 artifacts checked, 0 errors, 0 warnings;
- Workbench: 33,067 articles, 42,847 evidence excerpts and 36,648 result bundles;
- Article 1 rank-blind routes: B-NORM 85, C-STRUCT 316, union 351, overlap 50, unrouted 311;
- vocabulary audit completed: 27 B-NORM and 49 C-STRUCT phrases surfaced for human strategy review.

These values describe discovery, retrieval and reviewer-navigation infrastructure. They are **not** scientific inclusion counts and are **not** a PRISMA search result.

## Search architecture

### B-NORM

Purpose: retrieve normative nutrition guidance, guidelines, consensus and professional/scientific statements.

Current status: `PRESS_ACCEPTED_PREFREEZE`.

The formal provider set is now prospectively limited to **PubMed, LILACS/BVS and SciELO**, the sources available to the project. **Scopus and Web of Science are excluded because the project has no access and must not be simulated.**

### C-STRUCT

Purpose: retrieve operational structures relevant to the research question without building one giant noisy OR block.

Current subroutes:

1. `C1-CARE-PROCESS` — Nutrition Care Process, models/pathways of care, MNT, prescription/counseling and professional care structures.
2. `C2-COMPETENCY-LITERACY` — food/nutrition/culinary literacy, food skills, competencies, food agency and professional competencies.
3. `C3-IMPLEMENTATION` — implementation/dissemination/quality-improvement and monitoring structures.
4. `C4-SOCIAL-CONTEXT` — social context/determinants, social and food environment, social support, commensality and family/shared meals.

PRESS reviewer Vagner (UnB) selected `ADOPT_C4` on 2026-09-28. C4 is therefore **adopted pre-freeze**, but is not yet a frozen/formal provider query until provider-native validation, satisfactory sentinel/known-item closure, GF-10 and query freeze close.

## What is deliberately NOT closed

The formal systematic-review search has **not** been executed.

Current gate state:

- human PRESS review: completed by Vagner (UnB), independent attestation recorded, final decision `ACCEPT`, P07 clarified as non-material;
- canonical PRESS record: `PASS` (human `ACCEPT`, no material revision);
- GF-10: not authorized;
- provider-specific query freeze: not complete;
- formal provider search: not executed;
- PRISMA formal-search event: not emitted.

Therefore no agent, reviewer or manuscript may describe the discovery corpus as the final formal systematic-review search.

## Remaining search gate

Before formal execution:

1. run provider-native validation for PubMed, LILACS/BVS and SciELO;
2. close sentinel/known-item recovery and reconcile the 14-versus-16 historical sentinel notation;
3. freeze/version the protocol and exact search strings prospectively;
4. explicit GF-10 authorization;
5. versioned provider-query freeze with checksums;
6. only then run `FORMAL` searches from zero and create PRISMA search events.

Scopus and Web of Science are not part of the formal provider set because access is unavailable. Their absence is recorded prospectively and they must not be simulated or silently substituted.

D01–D05 remain preserved as developmental QA. Their 100-record D02–D05 precision packet is optional audit material and is **not an autonomous gate** for PRESS PASS, GF-10 or query freeze after the 2026-09-28 pre-formal-search amendment.

## Canonical artifacts

Repository:

- `config/nutev/article1_search_master_v1.json` — machine-readable master state;
- `config/nutev/article1_query_draft_v1.json` — pre-PRESS query draft;
- `config/nutev/topic_profiles/article1_prefreeze_v1.json` — pre-freeze topic/competency registry;
- `docs/ARTICLE1_QUERY_DRAFT_PRESS.md` — query-draft rationale;
- `docs/ARTICLE1_ROUTE_REVIEW_QUEUES.md` — B-NORM/C-STRUCT route contract;
- `docs/ARTICLE1_VOCABULARY_AUDIT.md` — vocabulary-audit contract;
- `AI_CONTEXT.md` — shared ChatGPT/Claude entrypoint.

Production runtime authorities:

- `project_output_reference/scientific/deepening/<search_id>/tier-A/DEEPENING_MANIFEST.json`;
- `project_output_reference/scientific/review_queue/<search_id>/tier-A/REVIEW_QUEUE_MANIFEST.json`;
- `project_output_reference/scientific/review_routes/<search_id>/article1/ROUTE_QUEUE_MANIFEST.json`;
- `project_output_reference/scientific/review_routes/<search_id>/article1/VOCABULARY_AUDIT.json`;
- `project_output_reference/scientific/workbench/WORKBENCH_MANIFEST.json`;
- `project_output_reference/agent_context/article1/CONTEXT_MANIFEST.json` after the agent-context bundle is generated.

## Scientific boundaries

Never infer any of the following from the current search infrastructure alone:

- bank presence = inclusion;
- Tier A/B/C/D = evidence quality or risk of bias;
- structural quarantine = scientific exclusion;
- route membership = eligibility;
- machine relevance = accepted evidence;
- full-text retrieval = inclusion;
- discovery counts = PRISMA counts;
- excerpts/result bundles = accepted EvidenceClaims.

When runtime data and this static snapshot disagree, inspect the runtime manifest and report the discrepancy instead of silently overwriting history.
