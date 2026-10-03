# Article 1 — provider-native validation run — 2026-09-29

## Result

The bounded technical validation was executed against the prospective formal provider set.

### PubMed

All five routes executed successfully:

| Route | Native status | Total found | Returned for validation |
|---|---:|---:|---:|
| B-NORM | completed | 139,808 | 5 |
| C1-CARE-PROCESS | completed | 4,086 | 5 |
| C2-COMPETENCY-LITERACY | completed | 1,782 | 5 |
| C3-IMPLEMENTATION | completed | 1,875 | 5 |
| C4-SOCIAL-CONTEXT | completed | 7,656 | 5 |

This is technical native execution evidence only. It is not query freeze, formal search, screening, or PRISMA.

### LILACS/BVS

All five automated native requests returned:

`HTTP 403: native public search interface does not allow this automated request`

Status: `AUTOMATION_BLOCKED_NATIVE_MANUAL_VALIDATION_REQUIRED`.

### SciELO

All five automated native requests returned:

`HTTP 403: native public search interface does not allow this automated request`

Status: `AUTOMATION_BLOCKED_NATIVE_MANUAL_VALIDATION_REQUIRED`.

## Interpretation

A 403 response is an access/interface restriction and must not be interpreted as a scientific zero, failed search strategy, or absence of eligible records.

The remaining provider-native gate is therefore manual validation of the exact compiled search strings in the native LILACS/BVS and SciELO interfaces.

## Guardrails

- PRESS: PASS
- GF-10: not authorized
- query freeze: incomplete
- FORMAL search: not executed
- PRISMA event: not emitted
- eligibility decisions: none created
- Scopus/Web of Science: excluded unavailable providers, not simulated

## Provenance

- source main SHA: `30f6c1e360f436c6ceddb69575dfb9fdfb64c0e4`
- workflow run: `36616261357`
- workflow job: `109569911229`
- artifact ID: `11055680957`
- artifact ZIP SHA-256: `8e1e28af7eb0b3d79eb903826718662bf3996d250e0490500b9b1e296b01cafb`
