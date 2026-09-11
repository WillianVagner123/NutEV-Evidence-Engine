# Willian doctorate runtime status — Sprint 15

The doctorate is treated as a customer workload of the generic multi-tenant Engine.

## Article 1

Canonical repository state remains `DISCOVERY_CLOSED_FORMAL_SEARCH_PENDING_PRESS_FREEZE`. Discovery/retrieval infrastructure may be available in production, but it is not a formal PRISMA search. A1 runtime access requires the exact private application plus reviewed server-managed workspace/project owner pins.

The read-only production audit reports only whether a first-party A1 application is materially present, whether owner pins match it and whether the private agent-context manifest exists. It deliberately reports `formal_search_authorized=false`; technical deployment cannot approve PRESS or GF-10.

## Article 2

Target application is `WILLIAN_DOCTORATE_A2` / `INTEGRATIVE_REVIEW`. Initial workflow remains fail-closed at `LEGACY_BINDING` until reviewed `LegacyBindingEvidence` exists. The runtime audit may observe application/workflow state but never activates binding.

Historical `project_output*`, `busca2a`, `busca2b`, query text, search IDs or current login do not establish A2 ownership. Candidate runtime trees are counted only as `UNKNOWN_UNTIL_REVIEW`.

## Operational sequence

1. Deploy this Sprint 15 diagnostic after CI.
2. Automatically collect a sanitized read-only audit after the successful deploy.
3. If A1 application/pins are materialized and match, test A1 UI/runtime navigation without changing methodology.
4. For A2, use the observed workflow plus a separate read-only provenance inventory. Only reviewed evidence may later produce internal `LegacyBindingEvidence`.
5. Run thesis work through generic Search/Library/Human Review/Export primitives; never add a global special case to make A1/A2 pass.
