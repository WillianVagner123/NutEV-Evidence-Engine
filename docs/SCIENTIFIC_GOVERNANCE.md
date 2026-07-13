# Scientific Governance

This policy governs how NutEV/NutMEV produces, audits and represents evidence.
It is binding for the software and for anyone using its outputs.

## Non-negotiable principles

1. **A `RecommendationCandidate` is not a final recommendation.** Every
   computational output is a *candidate* pending human review. Nothing produced
   automatically may be presented as a final clinical recommendation.
2. **Every claim must be traceable.** Each claim must be linked to a source
   document and a verifiable location within it (identifier + locator). Claims
   without traceable provenance are not admissible.
3. **Conflicts cannot be hidden.** Conflicting evidence, disagreements between
   sources, and reviewer disagreements must be surfaced, not suppressed or
   averaged away silently.
4. **The LLM does not decide approval.** Language models may assist with
   organization, extraction and drafting, but must never define final approval or
   sign-off of a recommendation.
5. **Final decisions require human review.** A human reviewer is always in the
   loop before any recommendation is finalized. See
   `docs/AI_USE_AND_HUMAN_OVERSIGHT.md`.
6. **Demo data is not scientific evidence.** Synthetic/demo outputs exist to show
   the pipeline shape and must never be cited as evidence.
7. **Protected documents are not redistributed.** See
   `docs/COPYRIGHT_AND_FULL_TEXT_POLICY.md`.
8. **Share the minimum, verifiable reference.** Prefer sharing DOI, official URL,
   metadata and the minimum permitted excerpt over full text.
9. **No personal or clinical data in the repository.** Patient/participant data
   and personal data must never be committed. See `docs/DATA_GOVERNANCE.md`.
10. **Methodological changes are versioned.** Any change to methodology, scoring,
    ontology or rules is versioned and recorded (see
    `docs/CHANGELOG_METODOLOGICO.md` and `CHANGELOG.md`).

## Roles

- **Maintainers** — steward the codebase, CI and releases.
- **Human reviewers/adjudicators** — approve/reject RecommendationCandidates; own
  the human-review queue.
- **Contributors** — propose code, sources or methodology changes via PR/issue.

## Decision flow (summary)

```
sources → search → extract → engine (claims + candidates)
        → audit (traceability, conflicts) → human review/adjudication
        → (only then) protocol item
```

The engine may emit candidates and flag conflicts; only the human-review step can
promote a candidate toward a protocol item.

## Change control

- Methodology/rule/scoring/ontology changes: PR + methodology changelog entry +
  version bump.
- Software changes: PR + CI green + `CHANGELOG.md` entry.
- Governance changes: PR referencing the affected principle above.

See also: `docs/DATA_GOVERNANCE.md`, `docs/AI_USE_AND_HUMAN_OVERSIGHT.md`,
`docs/COPYRIGHT_AND_FULL_TEXT_POLICY.md`, `docs/REPRODUCIBILITY.md`.
