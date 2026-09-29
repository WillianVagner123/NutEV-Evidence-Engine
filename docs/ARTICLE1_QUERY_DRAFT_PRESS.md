# Article 1 query draft for PRESS

Status: `PRESS_ACCEPTED_PREFREEZE`. PRESS is complete; GF-10 remains closed.

## Why this draft exists

The Tier A discovery corpus was deepened, profiled, routed into rank-blind B-NORM and C-STRUCT reading queues, and subjected to deterministic title-vocabulary audit. That audit surfaced recurring terminology for human strategy review; it does not validate a formal search.

The production vocabulary audit for search `web_20260830T182743+0000_91bde5be` reported 85 B-NORM documents, 316 C-STRUCT documents, 27 B-NORM vocabulary-review candidates, and 49 C-STRUCT candidates. The audit SHA-256 recorded in the draft config is `62c8e76ca02ba8a4a725867e0ae853db6981794e5ef981983a2d316ef99e179f`.

## Methodological decision

### B-NORM

Keep the current normative architecture. The audit does not justify adding a new mandatory concept.

`clinical practice` is already represented whenever it occurs as `clinical practice guideline` because the route includes `guideline*`. `lifestyle medicine` is relevant to applicability but must not become a mandatory normative filter, because that would miss general nutrition guidance that is applicable to Lifestyle Medicine without using the label in the title/abstract.

Organization names, disease labels, geography, MASLD terminology, diabetes, obesity, and similar recurring phrases are not promoted to search terms.

Two variants are retained only for PRESS delta testing: `food based` as an orthographic variant and `healthy eating` as a possible nutrition anchor.

### C-STRUCT

Do not turn title-frequency output into a giant OR block. The most frequent uncovered phrases are dominated by dietary content (`dietary patterns`, `dietary guidelines`), study design (`systematic review`, `randomized controlled`) and disease/population language. Those terms describe the retrieved literature rather than the structural construct being searched.

C-STRUCT is therefore drafted as a union of independent subroutes:

1. `C1-CARE-PROCESS` — Nutrition Care Process, care models/frameworks/pathways, MNT, prescription/counseling, scope of practice and models of care.
2. `C2-COMPETENCY-LITERACY` — food/nutrition/culinary literacy, food/cooking/meal skills, food agency, resource management and professional nutrition competencies.
3. `C3-IMPLEMENTATION` — implementation, dissemination, quality-improvement and monitoring structures anchored to nutrition/diet/practice.
4. `C4-SOCIAL-CONTEXT` — a PRESS-only candidate. The research question explicitly contains social contexts of eating, but the current pre-freeze topic registry has no dedicated retrieval route for that concept. It must be stress-tested independently before adoption.

Generic stage terms such as assessment, counseling, prescription, monitoring and follow-up remain important for extraction and coding, but are not approved as standalone retrieval terms because they are too broad.

## Formal provider set after PRESS

The prospective formal provider set is now limited to:

- PubMed;
- LILACS/BVS;
- SciELO.

Scopus and Web of Science are excluded because the project does not have access. They must not be simulated, and their absence must remain explicit in the methods and search provenance. The Engine may compile and validate only the providers in the formal set.

## PRESS requirements before GF-10

PRESS review is complete with `ACCEPT`. The remaining pre-freeze work is provider-native validation of PubMed, LILACS/BVS and SciELO, sentinel/known-item closure, prospective versioning and GF-10 authorization.

The preserved developmental QA delta tests are:

- B-NORM baseline vs `+ "food based"`;
- B-NORM baseline vs `+ "healthy eating"`;
- C1 with vs without `meal plan*`;
- C3 implementation-only incremental yield and manual precision sample;
- C4 social-context incremental yield and manual precision sample.

D01–D05 are developmental QA and are not an autonomous gate. No provider-specific string becomes FORMAL until provider-native validation and sentinel/known-item closure are documented, GF-10 is explicitly authorized, and the exact query is version-frozen.

## Scientific boundary

This draft does not include/exclude any document, emit a ScreeningDecision, create a PRISMA event, validate completeness, or infer quality, risk of bias, certainty, causality or recommendations. Discovery-corpus frequency is not treated as search validation.
