# Sprint 15 — Production UX + Internal Operations + Willian Doctorate Live

Status: **IN PROGRESS**. Baseline production release: NutEV 1.1.0, main `b8e6d262bec30bb704515be26f5f540eaf0719f8`.

## Purpose

Move acceptance from infrastructure correctness to practical research use. The sprint has three independent gates:

1. **USER_ACCEPTANCE** — a researcher can understand the first steps, select context, configure a project, search, organize evidence and reach review/export without developer knowledge.
2. **INTERNAL_OPERATIONS** — support can explain account/workspace/project/application/runtime state without editing SQLite or reading scientific payloads.
3. **WILLIAN_DOCTORATE_RUNTIME** — A1/A2 are observed as private applications of the generic Engine. Observation never grants scientific approval or historical ownership.

## Severity

- P0: task cannot be completed or risks data/privacy integrity.
- P1: normal user cannot understand or safely complete a core task without technical assistance.
- P2: material friction, avoidable ambiguity or excessive steps.
- P3: cosmetic/polish.

Only P0/P1 automatically block production acceptance. P2 is fixed when low-risk and clearly useful; P3 belongs in backlog.

## Current gates

| Gate | State | Evidence / next action |
|---|---|---|
| First login without workspace explains what is missing | PATCHED / CI PENDING | context guidance + Chromium fixture |
| First project without application presents understandable templates | EXISTING + TEST ADDED | configure one application and expose next actions |
| Cross-tenant privacy / stale-context browser matrix | PASS on 1.1.0 baseline | existing 12-scenario production-candidate evidence |
| Researcher primary navigation | REVIEWING | Project, Search, Library, Exports are primary; Review remains under advanced |
| Internal read-only support snapshot | DESIGNING | operator/runtime audit must expose state without private payload |
| A1 materialization / owner pins | PRODUCTION AUDIT PENDING | `audit_doctorate_runtime.py` after successful deploy |
| A2 application/workflow state | PRODUCTION AUDIT PENDING | read-only; no LegacyBindingEvidence is created |
| A1 formal scientific search | BLOCKED_SCIENTIFIC | PRESS/GF-10/freeze still required |
| A2 historical binding | BLOCKED_PROVENANCE until evidence | directory/search names never prove ownership |

## Acceptance journey

`login -> understand access -> workspace -> project -> application -> search -> Library -> review -> export -> audit`

The product must always answer four questions in plain language: **where am I, what can I do now, what is blocked, who/what unblocks it?** Technical IDs remain available in advanced details, not as the main instruction.

## Non-goals

No public self-signup; account/workspace provisioning remains administrative. No taxonomy/query/scoring expansion. No PRESS/GF-10 invention. No A2 binding by old folder/search names. No production destructive test. No clinical/research data in public CI artifacts.
