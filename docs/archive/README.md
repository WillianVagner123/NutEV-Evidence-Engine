# NutEV documentation archive

This directory preserves historical evidence that is useful for audit/provenance but no longer defines the current supported product.

## Rule

A document in `docs/archive/` may describe a real observation or decision from an earlier SHA/sprint. It must **not** be read as the current contract of `main` unless a current document explicitly incorporates it.

Current product documentation is indexed by [`../README.md`](../README.md).

## 2026 historical records

The `2026/` directory contains superseded closeout, smoke, migration, sprint and implementation-stage evidence, including:

- `ARTICLE1_D132_REVIEW_PORTAL.md` — PR-9 implementation specification for the private D-132 portal; preserved for provenance, not current product navigation;
- `ARTICLE1_FORMAL_GATE_STATUS.md` — dated Article 1 gate snapshot from 2026-09-10;
- `ARTICLE2_INTEGRATIVE_WORKFLOW.md` — PR-10 implementation specification for the Article 2 adapter;
- `ARTICLE2_LEGACY_BINDING_AUDIT.md` / `.json` — dated 2026-09-10 blocker/audit evidence; not current runtime state and not `LegacyBindingEvidence`;
- `CLOSEOUT_BASELINE.md` — closeout baseline from an earlier repository state;
- `DATA_INTEGRITY_CLOSEOUT.md` — historical data-integrity closeout;
- `HUMAN_REVIEW_ENGINE.md` — PR-8 implementation-stage specification, including deployment assumptions that were later superseded;
- `INTERNAL_OPERATIONS_AUDIT.md` — Sprint 15 operator audit/plan;
- `MULTITENANT_AUTH_SESSION.md` — PR-2 authentication/session migration note; the live contract remains at `docs/MULTITENANT_AUTH_SESSION.md`;
- `MULTITENANT_IDENTITY_CONTRACTS.md` — PR-1 contract snapshot from before login/session and production endpoint integration;
- `MULTITENANT_MIGRATION_INVENTORY.md` — PR-0 inventory captured before the authenticated multi-tenant architecture existed;
- `PRODUCTION_SMOKE_REPORT.md` — production smoke evidence from an earlier deployment state;
- `PRODUCT_DEATH_TEST_REPORT.md` — product/tenant death-test report from 2026-09-10, before final production/publication closeout;
- `REFERENCE_ENGINE_CLEANUP_AUDIT.md` — historical repository-reduction audit;
- `SECURITY_RED_TEAM_CLOSEOUT.md` — historical red-team closeout;
- `SPRINT15_PRODUCT_ACCEPTANCE_MASTER.md` — Sprint 15 acceptance record;
- `VALIDATED_WINDOWS_RUN_2026-08-18.md` — observed Windows execution from 2026-08-18;
- `WILLIAN_DOCTORATE_MIGRATION_DRY_RUN.md` — migration dry-run evidence;
- `WILLIAN_DOCTORATE_RUNTIME_STATUS.md` — Sprint 15 doctorate runtime plan/status snapshot.

Historical release notes such as `docs/RELEASE_V1_0_0.md` remain outside this archive because they are stable public release records, not transient sprint evidence.

## Removed transient files

Some files are not archived because Git already preserves their history and the files had no continuing audit value in the working tree. Examples include a superseded release-candidate note and pre-merge/pre-SSH disposition documents.

This cleanup does not delete Git history and does not modify the immutable `v1.1.0` release tag.
