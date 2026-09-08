# Article 1 — D-132 reviewer verification workflow

**Status:** `PROPOSED_PENDING_ADVISOR_APPROVAL`

This document mirrors methodological decision **D-132** from the canonical Article 1 Google Sheet. It is an operational contract for NutEV Evidence Engine and agents; it does **not** approve the methodology by itself.

## Human review model proposed in D-132

### Title and abstract

- R1 screens 100% of records.
- A human verifier independently checks an initial stratified random sample of 20% of R1 decisions.
- All records marked `DÚVIDA` or borderline by R1 are included in human verification.
- When operationally possible, the verifier must not see R1's decision before recording their own decision.
- For operational screening, `DÚVIDA` advances rather than being excluded.

### Full text

- R1 assesses 100% of full-text records.
- The human verifier independently reassesses 100% of R1 exclusions.
- The verifier reassesses 100% of `DÚVIDA` cases.
- The verifier also reassesses an initial random 20% sample of R1 inclusions.

### Extraction

- R1 performs 100% of scientific extraction.
- The human verifier checks an initial random 20% sample of included documents.
- All fields/cases marked `DÚVIDA` or critical are checked by the human verifier.

The 20% fraction is a prospective Article 1 protocol choice. It is **not** represented as a JBI-required percentage and may be changed only prospectively, before formal screening, through a recorded methodological decision.

## What NutEV Evidence Engine may do

The Engine may support the process by:

1. building the eligible sampling frame;
2. generating a deterministic random sample after the sampling seed/rule is frozen;
3. preparing R1 and verifier work queues;
4. keeping R1 and verifier decisions in separate fields/artifacts;
5. identifying conflicts only after both human decisions exist;
6. generating divergence/audit reports;
7. preparing locators, document navigation and evidence excerpts for human review;
8. exporting the human decisions to the canonical operational Sheet under the existing `ENGINE_TO_SHEET` governance.

## What NutEV Evidence Engine must never do

The Engine, ChatGPT, Claude or another automated agent must not:

- be counted as the second human reviewer/verifier;
- make the scientific inclusion or exclusion decision;
- adjudicate a human disagreement;
- silently replace or overwrite a human decision;
- convert discovery, ranking, routing, retrieval or machine relevance into eligibility;
- create formal PRISMA counts from PILOT, staging, discovery or machine queues.

## Formal gate

Formal screening remains blocked until both conditions are met:

1. D-132 is approved/frozen by the academic governance of Article 1; and
2. a human verifier is nominally designated.

PRESS/search-PILOT work may proceed according to its own gates. This reviewer-verification contract does not authorize GF-10, search freeze, formal screening or PRISMA.

## Canonical linkage

- Google Sheet: `A1 — BASE OPERACIONAL DA REVISÃO DE ESCOPO — CANÔNICA`
- Decision: `01_DECISOES_METODOLOGICAS!A135:H135` (`D-132`)
- Screening gate: `09H_GATE_CALIBRACAO_TRIAGEM`
- Preflight gate: `02J_PREFLIGHT_PILOT`, item `PF-13`
- Machine-readable mirror: `config/nutev/article1_reviewer_verification_d132.json`

When this repository snapshot and the canonical Drive governance disagree, the discrepancy must be surfaced. No agent may silently promote the repository proposal to an approved scientific decision.
