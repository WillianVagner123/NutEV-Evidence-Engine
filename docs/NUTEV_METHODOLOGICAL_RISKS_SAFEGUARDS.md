# NutEV Methodological Risks, Safeguards and Validation Criteria

This document converts the main scientific and technical vulnerabilities of the NutEV/NutMEV project into explicit safeguards. It is intended to protect the qualification text, articles and public repository from overclaiming.

## Core principle

NutEV is a methodological and scientific architecture for translating evidence into auditable recommendation candidates. It must not be presented as a final dietary protocol until a real run and human review validate the full evidence-to-protocol chain.

Safe wording:

```text
The NutEV platform provides an auditable architecture for translating evidence into recommendation candidates and protocol-readiness outputs, with human review safeguards.
```

Avoid:

```text
The NutEV platform has already generated final dietary recommendations.
```

---

## Risk register

| Risk | Why it matters | Safeguard |
|---|---|---|
| Scope too broad | Global food guidelines, clinical societies, dietary patterns, obesity and cardiometabolic conditions can become unmanageable. | Describe the search as systematic, traceable and updateable within eligible sources, not as absolute global exhaustiveness. |
| Review type ambiguous | Using exploratory/integrative/scoping interchangeably weakens the method. | Define Article 1 as a scoping review with documentary analysis and thematic synthesis. |
| Confusion between NutEV, Dieta NutEV, protocol, framework and pyramid | The thesis may look conceptually scattered. | Use the hierarchy defined in `docs/NUTEV_CONCEPTUAL_HIERARCHY.md`. |
| Calling NutEV a new diet too early | A reviewer may demand clinical superiority trials. | Present NutEV first as an evidence-translation protocol, not as a clinically proven superior diet. |
| Mixing population guidelines and clinical guidelines | They have different audiences and purposes. | Treat them as different evidence lenses: population baseline, clinical modifiers and intervention/pattern evidence. |
| Incomplete quality appraisal | Different source types cannot be weighed equally. | Use the source-specific plan in `docs/NUTEV_EVIDENCE_QUALITY_APPRAISAL_PLAN.md`. |
| Language and online-availability bias | Countries with better websites or English documents may be overrepresented. | Record language, accessibility, retrieval status, and metadata-only cases as limitations. |
| Fragile government websites | URLs change, PDFs disappear and scraping can fail. | Store URL, access date, document version, file hash when possible and failure reason. |
| Metadata-only records used as evidence | A document identified but not read cannot support a strong claim. | Metadata-only records may support identification, but not final claims without human review or full text. |
| Automatic claim extraction misses complex recommendations | Deterministic extraction can undercapture nuanced recommendations. | Validate extraction on a manual sample and refine domain lexicons iteratively. |
| False confidence in anti-hallucination safeguards | Quote-level traceability reduces but does not eliminate interpretive errors. | Keep human review mandatory for unsupported, inference-only or conflicting items. |
| Human review underspecified | Reviewers may ask who reviewed and how disagreement was resolved. | Use reviewer 1, reviewer 2, adjudicator, decision status and agreement metrics when real runs begin. |
| Protocol readiness appears arbitrary | Scores can look subjective. | Require document, claim, quote/support, quality status, no unresolved conflict and human review. |
| Software overengineering | The thesis may look like a software project rather than nutrition science. | State that the system is a methodological instrument; the scientific product is the NutEV dietary protocol. |
| Dashboard failure during qualification | A live interface can fail. | Always have exported Excel/PDF/Markdown outputs and screenshots as fallback. |
| Demo data confused with scientific result | Demo outputs are visually persuasive but simulated. | Keep `is_demo_data=true` and label demo outputs as non-scientific. |
| No real pilot yet | Architecture alone is not enough for strong claims. | Run a 20-30 document real pilot using `docs/NUTEV_REAL_PILOT_VALIDATION_PROTOCOL.md`. |
| Gap between candidate and final protocol item | RecommendationCandidate may be mistaken for final guidance. | Use the explicit status ladder from candidate to final protocol item. |
| Missing protocol versioning | The NutEV protocol will evolve over time. | Use the versioning rules in `config/nutev_protocol_versioning.json`. |
| Pyramid looks opinion-based | A visual pyramid can be challenged if not evidence-linked. | Each pyramid layer must link to domains, claims, documents, evidence quality and human review. |
| Master pipeline does not fully generate all second-layer outputs | Demo-data and helpers can work while the real pipeline remains incomplete. | The main pipeline must generate claims, recommendations, conflicts, gaps and readiness from the same real run. |
| Unit tests pass but integration fails | Real URLs, PDFs, encodings and sites can break. | Add a small real-run integration fixture and acceptance checklist. |
| Windows dependency fragility | Python versions and compiled packages may fail. | Standardize development on Python 3.12 and document Windows commands. |
| Streamlit mistaken for clinical platform | A dashboard is not a validated clinical system. | Present Control Center as local inspection/review UI only. |
| API keys in the UI | Secrets can leak into logs or outputs. | Prefer environment variables or `.env.local`; never write secrets to docs/logs/matrices. |
| Unclear central research question | The project may look like multiple products. | Use a single central question tied to evidence integration and protocol development. |
| Outcomes not condition-specific | DM, hypertension and dyslipidemia require different outcomes. | Use disease-specific outcome matrices. |
| GLP-1 and bariatric surgery expand scope | They can overtake the thesis. | Treat them as clinical modifiers or future subgroup analyses unless explicitly scoped. |
| Nutrition Contingency framework steals focus | It can become a second thesis. | Keep it as a complementary product/article, not the central thesis backbone. |
| No rule from evidence to menus | The protocol promises menus/pyramid but needs translation rules. | Use evidence -> principle -> food group -> portion/faixa -> clinical modifier -> meal example. |

---

## Status ladder for protocol items

Use this sequence to prevent confusion between draft and final outputs:

```text
draft_needs_evidence
ready_for_human_review
approved_candidate
protocol_ready
locked_protocol_item
final_protocol_item
```

Definitions:

- `draft_needs_evidence`: item has insufficient claim/document support.
- `ready_for_human_review`: item has support but still needs review.
- `approved_candidate`: reviewer approved candidate as methodologically acceptable.
- `protocol_ready`: item satisfies evidence, quality and conflict criteria.
- `locked_protocol_item`: item is locked into a versioned protocol draft.
- `final_protocol_item`: item is included in the final approved NutEV protocol version.

---

## Required rule for final protocol inclusion

A recommendation may enter the final protocol only if all conditions are met:

1. real document or validated source;
2. unique `document_id`;
3. extracted or manually validated claim;
4. `claim_id` linked to the document;
5. supporting quote or explicit human validation;
6. evidence quality classification;
7. no unresolved conflict;
8. human review completed;
9. protocol readiness calculated;
10. protocol version recorded.

If any item is missing, the output remains a candidate, gap or review item.

---

## Safe thesis language

Use:

```text
A real-run pilot will be used to test whether the full NutEV evidence-to-protocol workflow generates traceable claims, recommendation candidates, gaps, conflicts and protocol-readiness outputs from real documents.
```

Avoid:

```text
The NutEV protocol recommendations were generated automatically by the platform.
```

Use:

```text
The Control Center is a local inspection and review interface.
```

Avoid:

```text
The Control Center is a validated clinical decision system.
```

---

## Qualification fallback package

For every live demonstration, prepare:

1. dashboard running locally;
2. screenshots of Launchpad, Evidence Engine, Audit Engine, Human Review and Export Center;
3. exported Excel matrices;
4. `NUTEV_METHODS_MASTER.md`;
5. `NUTEV_SCIENTIFIC_RIGOR_REPORT.md`;
6. real-run limitations note;
7. pilot validation checklist.

This prevents the scientific argument from depending only on the live app.