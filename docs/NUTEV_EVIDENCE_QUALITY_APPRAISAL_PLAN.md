# NutEV Evidence Quality Appraisal Plan

This document defines how different source types should be appraised before they influence NutEV recommendation candidates or protocol-ready items.

## Why this is needed

NutEV integrates heterogeneous sources:

- national food-based dietary guidelines;
- clinical society guidelines;
- consensus statements;
- systematic reviews;
- meta-analyses;
- clinical trials;
- implementation studies;
- grey literature;
- methodological outputs.

These sources do not have the same purpose or evidence level. They should not be treated as equivalent.

## Source-specific appraisal plan

| Source type | Main role in NutEV | Suggested appraisal approach | Can support final protocol alone? |
|---|---|---|---|
| National food-based dietary guideline | Population baseline and public-health guidance | Documentary analysis; transparency criteria; optional AGREE II adaptation | Not alone for clinical modifiers |
| Clinical society guideline | Disease-specific modifier | AGREE II or structured guideline quality checklist | Yes, if current and human-reviewed |
| Consensus/position/scientific statement | Expert and society synthesis | Structured source credibility and conflict-of-interest appraisal | Conditional |
| Systematic review/meta-analysis | Evidence synthesis for dietary patterns/interventions | AMSTAR 2 or equivalent | Yes, if high/moderate quality and applicable |
| RCT/pragmatic trial | Intervention evidence | RoB 2 or equivalent | Conditional; usually stronger with synthesis |
| Non-randomized intervention | Implementation or pragmatic evidence | ROBINS-I or JBI | Conditional |
| Qualitative/implementation study | Feasibility, adherence, context | JBI or CASP qualitative/implementation checklist | Supports implementation components, not clinical efficacy alone |
| Grey literature/technical report | Contextual or policy evidence | Source credibility, transparency and relevance checklist | Usually no, unless corroborated |
| Computational inference | Hypothesis or triage aid | Must be marked inference-only | No |

## Minimum fields for quality appraisal

Every claim or recommendation candidate should eventually carry:

```text
evidence_type
evidence_quality_tier
quality_tool_or_rule
quality_rationale
applicability_to_population
clinical_condition
conflict_of_interest_note
human_quality_reviewer
quality_review_status
```

## Evidence tiers

Suggested tiers:

```text
normative_high
research_high
research_moderate
contextual
inference_only
insufficient
not_assessed
```

Definitions:

- `normative_high`: official guideline, clinical guideline or major scientific society statement with transparent scope.
- `research_high`: systematic review, meta-analysis or umbrella review with acceptable quality.
- `research_moderate`: RCT, pragmatic trial, or strong implementation study.
- `contextual`: grey literature, technical report or local policy document.
- `inference_only`: computational inference not yet supported by claim/quote/human review.
- `insufficient`: evidence is too weak or missing for protocol use.
- `not_assessed`: identified but not yet appraised.

## Recommendation strength

Recommendation strength should not be inferred only from document count.

Consider:

1. quality of source;
2. recency;
3. population applicability;
4. clinical condition applicability;
5. convergence across evidence lenses;
6. consistency of direction;
7. feasibility/implementation evidence;
8. human review and adjudication.

## Safe rule

A recommendation candidate may be discussed as protocol-ready only when:

```text
supporting claim + supporting document + quality appraisal + no unresolved conflict + human review
```

## What not to do

Do not use:

- metadata-only records as strong evidence;
- computational inference as final evidence;
- old guidelines as current without version/date review;
- demo-data as scientific appraisal;
- number of documents alone as proof of strength.

## Article wording

Use:

```text
Evidence sources will be classified by source type and appraised with source-appropriate criteria before being translated into recommendation candidates.
```

Avoid:

```text
All documents were treated equally as evidence for the protocol.
```