# NutEV AI Context — shared agent entrypoint

This file is the shared starting point for ChatGPT/Codex, Claude and other agents working on NutEV. It points to current sources of truth; it is not itself scientific evidence.

## Read first

For repository/product work:

1. `AGENTS.md` — repository invariants and release rules.
2. `README.md` — current supported product, release and production state.
3. `docs/README.md` — current documentation index; material under `docs/archive/` is historical unless a live contract explicitly incorporates it.

For Article 1 scientific work also read:

1. `ARTICLE1_SEARCH_MASTER.md` — canonical human-readable A1 search state;
2. `config/nutev/article1_search_master_v1.json` — machine-readable A1 state;
3. `config/nutev/article1_query_draft_v1.json` — current pre-PRESS query/route draft;
4. `docs/ARTICLE1_AGENT_CONTEXT.md` — contract for the private rank-blind agent bundle.

Claude Code may also read `CLAUDE.md`; it must not maintain a separate scientific truth from these shared sources.

## Private runtime context

The Article 1 agent bundle, when materialized, lives on private persistent runtime storage:

```text
project_output_reference/agent_context/article1/
  CONTEXT_MANIFEST.json
  SEARCH_STATE.json
  SEARCH_SUMMARY.md
  ARTICLE_SUMMARIES.jsonl
```

It is navigation/context infrastructure, not a public download surface. Hosted access must remain behind the authenticated workspace/project/application authorization boundary and the server-managed A1 owner pins required by the current deployment contract.

Do not infer ownership from labels, paths, folder names, the current login or a writable `assembly_id`.

`ARTICLE_SUMMARIES.jsonl` is intentionally rank-blind and must not expose full text, Bank rank/score/tier, machine-relevance score/band, eligibility decisions or PRISMA decisions.

## Hosted product boundary

The accepted hosted v1.1.0 baseline uses `NUTEV_AUTH_MODE=pilot`.

Legacy unscoped Workbench guidance such as direct `/api/articles/{document_id}` access is compatibility-only and must not be treated as the tenant-safe hosted API. Use the authorized Evidence Library and current project-scoped adapters for hosted work.

Outer proxy/Caddy controls do not replace application authentication or tenant/project authorization.

## Article 1 scientific boundary

Software production/publication does not open the A1 academic gates.

Discovery/harvest and technical routing are not a formal systematic-review search. Until canonical academic evidence records otherwise:

```text
PRESS PASS        = not inferred
GF-10             = not inferred
database queries  = not treated as frozen unless explicitly version-frozen
formal PRISMA     = not inferred from discovery/ranking/routing
```

Agents must retrieve the current canonical A1 master/runtime evidence before making a mutable status claim and must expose disagreement or missing evidence instead of guessing.

## Article 2 scientific boundary

A2 remains fail-closed unless reviewed provenance satisfies the `LegacyBindingEvidence` contract. A deployed route, project name, historical workstream label or current user session is not ownership evidence.

## Good agent behavior

Agents should:

- distinguish immutable release identity, moving `main`, production runtime and scientific state;
- cite/record the relevant SHA, manifest and hashes for concrete runtime claims;
- prefer current runtime manifests for mutable production observations;
- treat agent bundles as navigation/context, not evidence adjudication;
- never convert ranking, route membership or model output into inclusion/exclusion, quality, certainty, recommendation or PRISMA state;
- never fabricate provider results, counts, identifiers, DOI/PMID/URLs, human review or scientific approval;
- treat `docs/archive/` as historical provenance rather than the current operational contract.

## Current software publication identity

```text
version: 1.1.0
immutable tag: v1.1.0
release SHA: 49588233ad2828b8fcc6140398ab55aedf7c03ef
Zenodo record: 22726717
DOI: 10.5281/zenodo.22726717
```

The moving `main` may contain validated post-release fixes/documentation. Never move/recreate `v1.1.0` to follow `main`.
