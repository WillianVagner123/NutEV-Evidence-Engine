# Scientific Validation Status

Current scientific verdict: **B — DEMOTE**  
Meaning: NutEV is an operational/experimental reference-discovery utility; scientific incremental benefit over declared baselines has not yet been demonstrated.

## Current product identity

The current supported software release is separate from the historical validation freeze:

```text
stable_release = v1.1.0
immutable_release_sha = 49588233ad2828b8fcc6140398ab55aedf7c03ef
zenodo_record = 22726717
doi = 10.5281/zenodo.22726717
software_publication = COMPLETE
scientific_verdict = B — DEMOTE
```

GitHub/Zenodo publication, production acceptance and a green engineering pipeline do **not** promote the scientific verdict.

## Historical validation freeze

The following identifiers are intentionally preserved because they define the runtime candidate frozen for the scientific benchmark. They are **historical validation identities**, not the current stable software release:

```text
historical_engineering_gate_base = 6070e89786eb0164a9a8d8531effe8e3703d1845
frozen_validation_runtime_candidate = 6aa7a5fe6009776e611ca3e1506486606b05f4f6
canonical_taxonomy = 2026-08-v2
guardrail_policy = 2026-08-18.2
```

The former `v1.0.0` release remains immutable historical evidence, but it is no longer the current stable release. The current stable release is `v1.1.0`.

## Evidence status

| Domain | Status | Current evidence |
|---|---|---|
| Software executes deterministically for fixed inputs/config | OBSERVED | Unit/integration tests and audited runtime contracts |
| Input/output integrity via hashes | OBSERVED | Guardrails and `AUDIT_MANIFEST.json` |
| Canonical taxonomy structure | OBSERVED | Registry, fail-closed mapping, taxonomy tests |
| Scientific retrieval recall | NOT_TESTED | No independent gold standard yet |
| Scientific retrieval precision | NOT_TESTED | No independent gold standard yet |
| MAP/MRR/nDCG versus baselines | NOT_TESTED | No comparative benchmark yet |
| Taxonomy validity versus human experts | NOT_TESTED | Structural tests are not scientific validation |
| Work-level deduplication precision/recall | NOT_TESTED | Canonical exact identity is not semantic/work-level validation |
| Provider incremental value | NOT_TESTED | No leave-one-provider-out benchmark |
| Provider weight validity | NOT_TESTED | Weights remain engineering heuristics |
| Metadata availability bias | NOT_TESTED | No controlled perturbation study |
| Quarantine recall loss | NOT_TESTED | No human review sample of quarantined relevant records |
| Ranking sensitivity | NOT_TESTED | No systematic parameter perturbation benchmark |
| User workload benefit | NOT_TESTED | No controlled user study |
| Generalization to external questions | NOT_TESTED | No sealed external test set |

## Engineering and repository governance

The engineering gate for the historical frozen candidate remains PASS. Current repository governance has also advanced since that freeze.

| Requirement | Status | Evidence |
|---|---|---|
| Taxonomy registry and exclusion of historical workstreams | PASS | Registry and regression tests |
| Document type separated from taxonomy | PASS | Taxonomy registry tests |
| Input SHA-256 fail-closed | PASS | Guardrail contract |
| Invalid identifier cannot qualify as `A_IDENTIFIER` | PASS | Shared DOI/PMID/PMCID validators + regression tests |
| Invalid identifier never repaired by inference | PASS | Malformed values remain unchanged; URL fallback/quarantine is explicit |
| Consistency between identifier validity and identifier score bonus | PASS | Traceability and scoring share the validated identifier contract |
| Same canonical identity normalization in collection and ranking | PASS | Shared `src/nutev/reference_identity.py` contract |
| README/limitations aligned with scientific boundary | PASS | Public docs retain `B — DEMOTE` and ranking limitations |
| `main` protected against deletion/non-fast-forward | PASS_CURRENT_REPO | Active `Protect main` repository ruleset |
| PR and strict required status checks on `main` | PASS_CURRENT_REPO | Active `Protect main` repository ruleset, no bypass actor |
| Production promotion requires full exact-SHA product gate | PASS_CURRENT_REPO | Deploy prerequisite barrier requires all seven release workflows |

The historical governance gap recorded during the original validation freeze is therefore **resolved for the current repository**. This does not retroactively change the frozen scientific candidate or create scientific evidence.

## CI evidence for frozen runtime candidate

GitHub Actions on `6aa7a5fe6009776e611ca3e1506486606b05f4f6` recorded:

- tests Python 3.12: PASS;
- tests Python 3.13: PASS;
- Windows smoke Python 3.12: PASS;
- audit guardrail contract: PASS;
- typecheck provenance core: PASS;
- lint/compile: PASS;
- security scan: PASS;
- dependency review: PASS;
- release artifact validation: PASS;
- CodeQL: PASS.

## Freeze decision

**ENGINEERING GATE: PASS.**

**VALIDATION RUNTIME CANDIDATE: FROZEN at `6aa7a5fe6009776e611ca3e1506486606b05f4f6`.**

The freeze binds the runtime implementation used for the forthcoming scientific benchmark. The project remains scientifically `B — DEMOTE` because an independent retrieval benchmark has not yet demonstrated incremental benefit.

After this freeze:

- external-test labels must not be used to change ranking weights, queries, taxonomy or identity rules for this candidate;
- tuning, if needed, must use a declared development/validation set and produce a new candidate version;
- current product documentation may evolve without rewriting the frozen validation SHA;
- any runtime change creates a new validation candidate and invalidates direct attribution of later benchmark results to this historical SHA.

## Required scientific sequence

1. construct an independent gold standard without using NutEV rankings to define relevance;
2. seal the external-test partition;
3. generate identical-question outputs for NutEV and declared baselines;
4. compute precision/recall@k, MRR, MAP, nDCG and workload milestones;
5. run ablations and sensitivity analyses on permitted development/validation data;
6. validate taxonomy against independent human classifications;
7. benchmark work-level deduplication;
8. quantify provider contribution, metadata bias and quarantine recall loss;
9. open the sealed external-test set only after decisions are fixed;
10. issue the next scientific verdict A/B/C/D.

## Interpretation rule

Engineering success permits scientific testing; it is not scientific validation. Until an independent benchmark demonstrates otherwise, `B — DEMOTE` remains the defensible scientific verdict for the product.