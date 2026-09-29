# Article 1 — Methodological Amendment — Streamlined Pre-Freeze Gates

**ID:** `A1-AMEND-2026-09-28-STREAMLINED-PREFREEZE`  
**Date:** 2026-09-28  
**Timing:** before FORMAL search, before protocol/query freeze  
**Decision owner:** Willian Vagner  
**Supervisor approval:** not claimed by this record

## Decision

Reclassify D01–D05 delta tests and the 100-record D02–D05 human precision packet from **mandatory gate** to **developmental QA / optional audit evidence**.

They remain preserved with their technical counts, sample identities and custody, but they are no longer autonomous prerequisites for:

- canonical `PRESS=PASS`;
- GF-10;
- provider query freeze.

## Why this is methodologically acceptable

The core conduct/reporting requirements for the scoping review remain intact:

- explicit, comprehensive and transparent searching;
- full reproducible search strategies and limits;
- provider/platform/date recording;
- provider-native translation/validation before freeze;
- source selection at title/abstract and full text by two or more independent reviewers, with disagreements resolved by consensus or a third reviewer;
- auditable deduplication and full-text exclusion reasons;
- PRISMA-ScR / PRISMA-S reporting.

The independent PRESS review was completed by Vagner (UnB) with `ACCEPT`, no material revision, P07 explicitly clarified as non-material, and `ADOPT_C4`. The delta samples therefore remain useful development evidence without needing to become a second, separate human-review gate before formal identification.

## Standards basis

- JBI Manual for Evidence Synthesis, Scoping Reviews (2026): searching should be explicit, comprehensive and transparent; source selection at title/abstract and full text is performed by two or more reviewers independently.
- PRISMA-ScR: report information sources, full electronic strategy for at least one database, and source-selection methods.
- PRISMA-S / PRISMA expanded search guidance: when a search strategy is validated or peer reviewed, report that process and the tool used; this is a reporting requirement for a process when performed, not a universal requirement for a second 100-record delta review.

References:
- https://jbi-global-wiki.refined.site/space/MANUAL/355862497/10.%2BScoping%2Breviews%C2%A0
- https://jbi-global-wiki.refined.site/space/MANUAL/355862749/10.2.6%2BSearching%2Bfor%2Bthe%2Bevidence
- https://www.prisma-statement.org/scoping
- https://www.prisma-statement.org/prisma-search

## Human PRESS evidence

Reviewer: **Vagner — UnB**  
Decision: `ACCEPT`  
Independence attestation: yes  
P07: non-material observation; improve/close sentinels before freeze  
C4: `ADOPT_C4`

Canonical evidence:
`evidence/article1_press/article1_press_20260928T230157Z_vagner/PRESS_HUMAN_REVIEW.json`

The original evidence file is not rewritten; this amendment changes only the downstream gate policy.

## What remains mandatory before formal search

1. final formal provider set;
2. provider-native validation and cross-database translation;
3. satisfactory known-item/sentinel closure, including 14-versus-16 harmonization;
4. final versioned strings and checksums;
5. protocol freeze/registration;
6. GF-10 authorization;
7. query freeze;
8. FORMAL search from zero.

## Screening remains double-human

This amendment does **not** remove the planned independent dual review for title/abstract selection or full-text eligibility. Those stages remain human, independent and adjudicated as specified in the protocol.

## PRISMA boundary

D01–D05 remain PILOT/DEVELOPMENT evidence and do not contribute to PRISMA counts.
