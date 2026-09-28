# Article 1 — PRESS Packet v0.1

**Status:** `PREPARED_FOR_HUMAN_PRESS_REVIEW`. **Não** é `PRESS=PASS`.
Prepared: 2026-09-28. Canonical question synchronized on main `5adb56ccaf265b57b4085fdb3f960a371601fb58`.
Candidate package: `tools/build_article1_press_query_package.py` (no network), `package_sha256 = 82834c34c1a25d753263350e1367232621962f350c11880024049be4b5ec7a7c`, draft `article1-query-draft-v1`.
Canonical PRESS record (unchanged by this packet): `config/nutev/article1_press_review_v1.json` — `status=DRAFT`, `reviewer=null`, P01–P10 `PENDING`.

```text
PRESS_REVIEWER = HUMAN_DECISION_REQUIRED
```

## 1. Question and objective — read this first

The review question has now been harmonised and approved by Willian Vagner and supervisor Prof. Dr. Caio Eduardo G. Reis (2026-09-28):

> Como documentos normativos e estruturantes do cuidado alimentar de adultos formulam recomendações e direção dietética e em que medida as operacionalizam por meio de formas de prescrição, competências e repertórios, contexto, condições de execução, monitoramento e continuidade do cuidado?

The earlier manuscript, protocol and Engine formulations are retained in version history as provenance, but they no longer compete as active questions. PRESS P01 should now assess whether the candidate strategy faithfully translates this single canonical question.

## 2. Structure used (PCC)

From the manuscript/protocol (scoping review, JBI):

- **Population:** documents for adults or for professionals/teams/services providing adult dietary care; mixed populations if adult content is separable.
- **Concept:** recommendations/dietary direction and their documentary operationalization (prescription form, repertoires/competencies, context, implementation, monitoring, adaptation, maintenance). ABCD-NUT-EV is applied **after** eligibility, never as a retrieval or inclusion criterion.
- **Context:** public policy, primary care, outpatient/clinical care, community programmes, food education, digital/hybrid settings.
- **Document families (post-inclusion):** F1 FBDGs; F2 clinical guidelines/consensus/statements; F3 dietary patterns/strategies; F4 prescription and care models; F5 competencies/literacy; F6 implementation/monitoring; F7 conceptual/professional.

## 3. Master strategy (Engine, pre-PRESS)

```text
B-NORM   = nutrition_anchor AND normative_marker
C-STRUCT = C1 ∪ C2 ∪ C3 [∪ C4 if adopted], deduplicated
  C1-CARE-PROCESS        = professional_nutrition_anchor AND care_structure
  C2-COMPETENCY-LITERACY = nutrition_food_professional_anchor AND competency_or_literacy
  C3-IMPLEMENTATION      = nutrition_practice_anchor AND implementation_structure
  C4-SOCIAL-CONTEXT      = food_nutrition_anchor AND social_eating_context AND operational_marker   (PRESS_ONLY_CANDIDATE_NOT_APPROVED)
```

Block rationale (from `config/nutev/article1_query_draft_v1.json`):

- **B-NORM** keeps the baseline architecture; audit phrases were organisations, diseases, populations or geography and did not justify a new mandatory concept. `lifestyle medicine` is deliberately **not** a mandatory B-NORM filter.
- **C-STRUCT** is split into subroutes because a single structural OR imported discovery-corpus noise (dietary content, disease, population and design phrases).
- **Generic stage terms** (dietary/nutrition assessment, counseling, prescription, monitoring, follow-up) are not standalone retrieval terms; they are screening/extraction dimensions.
- **Disease and study-design terms** are not promoted from frequency.

## 4. Candidate strings by provider (compiled, NOT native-validated)
### PubMed

Status do compilador: `CANDIDATE_NOT_NATIVE_VALIDATED`

**B-NORM**

```text
(nutrition[Title/Abstract] OR diet*[Title/Abstract] OR food-based[Title/Abstract] OR "dietary pattern*"[Title/Abstract]) AND (guideline*[Title/Abstract] OR guidance[Title/Abstract] OR recommendation*[Title/Abstract] OR consensus[Title/Abstract] OR "position statement*"[Title/Abstract] OR "scientific statement*"[Title/Abstract] OR "professional statement*"[Title/Abstract] OR standard*[Title/Abstract])
```

**C1-CARE-PROCESS**

```text
(nutrition*[Title/Abstract] OR dietetic*[Title/Abstract] OR dietitian*[Title/Abstract] OR nutritionist*[Title/Abstract] OR "lifestyle medicine"[Title/Abstract]) AND ("nutrition care process"[Title/Abstract] OR "nutrition care model*"[Title/Abstract] OR "nutrition care framework*"[Title/Abstract] OR "nutrition care pathway*"[Title/Abstract] OR "nutrition pathway*"[Title/Abstract] OR "medical nutrition therapy"[Title/Abstract] OR "diet prescription*"[Title/Abstract] OR "dietary prescription*"[Title/Abstract] OR "nutrition prescription*"[Title/Abstract] OR "food prescription*"[Title/Abstract] OR "nutrition counseling"[Title/Abstract] OR "nutrition counselling"[Title/Abstract] OR "dietetic care"[Title/Abstract] OR dietitian-led[Title/Abstract] OR "scope of practice"[Title/Abstract] OR "clinical decision framework*"[Title/Abstract] OR "model of care"[Title/Abstract])
```

**C2-COMPETENCY-LITERACY**

```text
(nutrition*[Title/Abstract] OR dietitian*[Title/Abstract] OR nutritionist*[Title/Abstract] OR dietetic*[Title/Abstract] OR food[Title/Abstract] OR "lifestyle medicine"[Title/Abstract]) AND ("food literacy"[Title/Abstract] OR "nutrition literacy"[Title/Abstract] OR "culinary literacy"[Title/Abstract] OR "food skill*"[Title/Abstract] OR "cooking skill*"[Title/Abstract] OR "meal planning skill*"[Title/Abstract] OR "food competenc*"[Title/Abstract] OR "culinary competenc*"[Title/Abstract] OR "culinary medicine"[Title/Abstract] OR "food agency"[Title/Abstract] OR "food resource management"[Title/Abstract] OR "meal preparation skill*"[Title/Abstract] OR "shopping skill*"[Title/Abstract] OR "nutrition competenc*"[Title/Abstract] OR "dietitian competenc*"[Title/Abstract] OR "nutritionist competenc*"[Title/Abstract] OR "clinical nutrition skill*"[Title/Abstract] OR "competency framework*"[Title/Abstract] OR "nutrition counseling skill*"[Title/Abstract] OR "nutrition counselling skill*"[Title/Abstract] OR "dietetic competenc*"[Title/Abstract])
```

**C3-IMPLEMENTATION**

```text
(nutrition*[Title/Abstract] OR diet*[Title/Abstract] OR dietary[Title/Abstract] OR "nutrition care"[Title/Abstract] OR "lifestyle medicine"[Title/Abstract]) AND ("implementation framework*"[Title/Abstract] OR "implementation strateg*"[Title/Abstract] OR "implementation guide*"[Title/Abstract] OR "implementation toolkit*"[Title/Abstract] OR "implementation plan*"[Title/Abstract] OR "implementation model*"[Title/Abstract] OR "implementation project*"[Title/Abstract] OR "dissemination framework*"[Title/Abstract] OR "dissemination strateg*"[Title/Abstract] OR "guideline implementation"[Title/Abstract] OR "practice implementation"[Title/Abstract] OR "quality improvement framework*"[Title/Abstract] OR "quality improvement strateg*"[Title/Abstract] OR "monitoring framework*"[Title/Abstract] OR "monitoring system*"[Title/Abstract] OR "implementation monitoring"[Title/Abstract] OR "implementation evaluation"[Title/Abstract])
```

**C4-SOCIAL-CONTEXT**

```text
(nutrition*[Title/Abstract] OR diet*[Title/Abstract] OR food[Title/Abstract] OR eating[Title/Abstract]) AND ("social context*"[Title/Abstract] OR "social determinant*"[Title/Abstract] OR "social environment*"[Title/Abstract] OR "food environment*"[Title/Abstract] OR "social support"[Title/Abstract] OR commensality[Title/Abstract] OR "family meal*"[Title/Abstract] OR "shared meal*"[Title/Abstract]) AND (framework*[Title/Abstract] OR model*[Title/Abstract] OR guideline*[Title/Abstract] OR assessment[Title/Abstract] OR counseling[Title/Abstract] OR counselling[Title/Abstract] OR "care process"[Title/Abstract])
```

### LILACS/BVS

Status do compilador: `CANDIDATE_NOT_NATIVE_VALIDATED`

**B-NORM**

```text
(tw:nutrition OR tw:diet* OR tw:food-based OR tw:"dietary pattern*") AND (tw:guideline* OR tw:guidance OR tw:recommendation* OR tw:consensus OR tw:"position statement*" OR tw:"scientific statement*" OR tw:"professional statement*" OR tw:standard*)
```

**C1-CARE-PROCESS**

```text
(tw:nutrition* OR tw:dietetic* OR tw:dietitian* OR tw:nutritionist* OR tw:"lifestyle medicine") AND (tw:"nutrition care process" OR tw:"nutrition care model*" OR tw:"nutrition care framework*" OR tw:"nutrition care pathway*" OR tw:"nutrition pathway*" OR tw:"medical nutrition therapy" OR tw:"diet prescription*" OR tw:"dietary prescription*" OR tw:"nutrition prescription*" OR tw:"food prescription*" OR tw:"nutrition counseling" OR tw:"nutrition counselling" OR tw:"dietetic care" OR tw:dietitian-led OR tw:"scope of practice" OR tw:"clinical decision framework*" OR tw:"model of care")
```

**C2-COMPETENCY-LITERACY**

```text
(tw:nutrition* OR tw:dietitian* OR tw:nutritionist* OR tw:dietetic* OR tw:food OR tw:"lifestyle medicine") AND (tw:"food literacy" OR tw:"nutrition literacy" OR tw:"culinary literacy" OR tw:"food skill*" OR tw:"cooking skill*" OR tw:"meal planning skill*" OR tw:"food competenc*" OR tw:"culinary competenc*" OR tw:"culinary medicine" OR tw:"food agency" OR tw:"food resource management" OR tw:"meal preparation skill*" OR tw:"shopping skill*" OR tw:"nutrition competenc*" OR tw:"dietitian competenc*" OR tw:"nutritionist competenc*" OR tw:"clinical nutrition skill*" OR tw:"competency framework*" OR tw:"nutrition counseling skill*" OR tw:"nutrition counselling skill*" OR tw:"dietetic competenc*")
```

**C3-IMPLEMENTATION**

```text
(tw:nutrition* OR tw:diet* OR tw:dietary OR tw:"nutrition care" OR tw:"lifestyle medicine") AND (tw:"implementation framework*" OR tw:"implementation strateg*" OR tw:"implementation guide*" OR tw:"implementation toolkit*" OR tw:"implementation plan*" OR tw:"implementation model*" OR tw:"implementation project*" OR tw:"dissemination framework*" OR tw:"dissemination strateg*" OR tw:"guideline implementation" OR tw:"practice implementation" OR tw:"quality improvement framework*" OR tw:"quality improvement strateg*" OR tw:"monitoring framework*" OR tw:"monitoring system*" OR tw:"implementation monitoring" OR tw:"implementation evaluation")
```

**C4-SOCIAL-CONTEXT**

```text
(tw:nutrition* OR tw:diet* OR tw:food OR tw:eating) AND (tw:"social context*" OR tw:"social determinant*" OR tw:"social environment*" OR tw:"food environment*" OR tw:"social support" OR tw:commensality OR tw:"family meal*" OR tw:"shared meal*") AND (tw:framework* OR tw:model* OR tw:guideline* OR tw:assessment OR tw:counseling OR tw:counselling OR tw:"care process")
```

### SciELO

Status do compilador: `CANDIDATE_NOT_NATIVE_VALIDATED`

**B-NORM**

```text
(nutrition OR diet* OR food-based OR "dietary pattern*") AND (guideline* OR guidance OR recommendation* OR consensus OR "position statement*" OR "scientific statement*" OR "professional statement*" OR standard*)
```

**C1-CARE-PROCESS**

```text
(nutrition* OR dietetic* OR dietitian* OR nutritionist* OR "lifestyle medicine") AND ("nutrition care process" OR "nutrition care model*" OR "nutrition care framework*" OR "nutrition care pathway*" OR "nutrition pathway*" OR "medical nutrition therapy" OR "diet prescription*" OR "dietary prescription*" OR "nutrition prescription*" OR "food prescription*" OR "nutrition counseling" OR "nutrition counselling" OR "dietetic care" OR dietitian-led OR "scope of practice" OR "clinical decision framework*" OR "model of care")
```

**C2-COMPETENCY-LITERACY**

```text
(nutrition* OR dietitian* OR nutritionist* OR dietetic* OR food OR "lifestyle medicine") AND ("food literacy" OR "nutrition literacy" OR "culinary literacy" OR "food skill*" OR "cooking skill*" OR "meal planning skill*" OR "food competenc*" OR "culinary competenc*" OR "culinary medicine" OR "food agency" OR "food resource management" OR "meal preparation skill*" OR "shopping skill*" OR "nutrition competenc*" OR "dietitian competenc*" OR "nutritionist competenc*" OR "clinical nutrition skill*" OR "competency framework*" OR "nutrition counseling skill*" OR "nutrition counselling skill*" OR "dietetic competenc*")
```

**C3-IMPLEMENTATION**

```text
(nutrition* OR diet* OR dietary OR "nutrition care" OR "lifestyle medicine") AND ("implementation framework*" OR "implementation strateg*" OR "implementation guide*" OR "implementation toolkit*" OR "implementation plan*" OR "implementation model*" OR "implementation project*" OR "dissemination framework*" OR "dissemination strateg*" OR "guideline implementation" OR "practice implementation" OR "quality improvement framework*" OR "quality improvement strateg*" OR "monitoring framework*" OR "monitoring system*" OR "implementation monitoring" OR "implementation evaluation")
```

**C4-SOCIAL-CONTEXT**

```text
(nutrition* OR diet* OR food OR eating) AND ("social context*" OR "social determinant*" OR "social environment*" OR "food environment*" OR "social support" OR commensality OR "family meal*" OR "shared meal*") AND (framework* OR model* OR guideline* OR assessment OR counseling OR counselling OR "care process")
```

### Scopus

Status do compilador: `CANDIDATE_NOT_NATIVE_VALIDATED`

**B-NORM**

```text
TITLE-ABS-KEY(nutrition OR diet* OR food-based OR "dietary pattern*") AND TITLE-ABS-KEY(guideline* OR guidance OR recommendation* OR consensus OR "position statement*" OR "scientific statement*" OR "professional statement*" OR standard*)
```

**C1-CARE-PROCESS**

```text
TITLE-ABS-KEY(nutrition* OR dietetic* OR dietitian* OR nutritionist* OR "lifestyle medicine") AND TITLE-ABS-KEY("nutrition care process" OR "nutrition care model*" OR "nutrition care framework*" OR "nutrition care pathway*" OR "nutrition pathway*" OR "medical nutrition therapy" OR "diet prescription*" OR "dietary prescription*" OR "nutrition prescription*" OR "food prescription*" OR "nutrition counseling" OR "nutrition counselling" OR "dietetic care" OR dietitian-led OR "scope of practice" OR "clinical decision framework*" OR "model of care")
```

**C2-COMPETENCY-LITERACY**

```text
TITLE-ABS-KEY(nutrition* OR dietitian* OR nutritionist* OR dietetic* OR food OR "lifestyle medicine") AND TITLE-ABS-KEY("food literacy" OR "nutrition literacy" OR "culinary literacy" OR "food skill*" OR "cooking skill*" OR "meal planning skill*" OR "food competenc*" OR "culinary competenc*" OR "culinary medicine" OR "food agency" OR "food resource management" OR "meal preparation skill*" OR "shopping skill*" OR "nutrition competenc*" OR "dietitian competenc*" OR "nutritionist competenc*" OR "clinical nutrition skill*" OR "competency framework*" OR "nutrition counseling skill*" OR "nutrition counselling skill*" OR "dietetic competenc*")
```

**C3-IMPLEMENTATION**

```text
TITLE-ABS-KEY(nutrition* OR diet* OR dietary OR "nutrition care" OR "lifestyle medicine") AND TITLE-ABS-KEY("implementation framework*" OR "implementation strateg*" OR "implementation guide*" OR "implementation toolkit*" OR "implementation plan*" OR "implementation model*" OR "implementation project*" OR "dissemination framework*" OR "dissemination strateg*" OR "guideline implementation" OR "practice implementation" OR "quality improvement framework*" OR "quality improvement strateg*" OR "monitoring framework*" OR "monitoring system*" OR "implementation monitoring" OR "implementation evaluation")
```

**C4-SOCIAL-CONTEXT**

```text
TITLE-ABS-KEY(nutrition* OR diet* OR food OR eating) AND TITLE-ABS-KEY("social context*" OR "social determinant*" OR "social environment*" OR "food environment*" OR "social support" OR commensality OR "family meal*" OR "shared meal*") AND TITLE-ABS-KEY(framework* OR model* OR guideline* OR assessment OR counseling OR counselling OR "care process")
```

### Web of Science

Status do compilador: `CANDIDATE_NOT_NATIVE_VALIDATED`

**B-NORM**

```text
TS=(nutrition OR diet* OR food-based OR "dietary pattern*") AND TS=(guideline* OR guidance OR recommendation* OR consensus OR "position statement*" OR "scientific statement*" OR "professional statement*" OR standard*)
```

**C1-CARE-PROCESS**

```text
TS=(nutrition* OR dietetic* OR dietitian* OR nutritionist* OR "lifestyle medicine") AND TS=("nutrition care process" OR "nutrition care model*" OR "nutrition care framework*" OR "nutrition care pathway*" OR "nutrition pathway*" OR "medical nutrition therapy" OR "diet prescription*" OR "dietary prescription*" OR "nutrition prescription*" OR "food prescription*" OR "nutrition counseling" OR "nutrition counselling" OR "dietetic care" OR dietitian-led OR "scope of practice" OR "clinical decision framework*" OR "model of care")
```

**C2-COMPETENCY-LITERACY**

```text
TS=(nutrition* OR dietitian* OR nutritionist* OR dietetic* OR food OR "lifestyle medicine") AND TS=("food literacy" OR "nutrition literacy" OR "culinary literacy" OR "food skill*" OR "cooking skill*" OR "meal planning skill*" OR "food competenc*" OR "culinary competenc*" OR "culinary medicine" OR "food agency" OR "food resource management" OR "meal preparation skill*" OR "shopping skill*" OR "nutrition competenc*" OR "dietitian competenc*" OR "nutritionist competenc*" OR "clinical nutrition skill*" OR "competency framework*" OR "nutrition counseling skill*" OR "nutrition counselling skill*" OR "dietetic competenc*")
```

**C3-IMPLEMENTATION**

```text
TS=(nutrition* OR diet* OR dietary OR "nutrition care" OR "lifestyle medicine") AND TS=("implementation framework*" OR "implementation strateg*" OR "implementation guide*" OR "implementation toolkit*" OR "implementation plan*" OR "implementation model*" OR "implementation project*" OR "dissemination framework*" OR "dissemination strateg*" OR "guideline implementation" OR "practice implementation" OR "quality improvement framework*" OR "quality improvement strateg*" OR "monitoring framework*" OR "monitoring system*" OR "implementation monitoring" OR "implementation evaluation")
```

**C4-SOCIAL-CONTEXT**

```text
TS=(nutrition* OR diet* OR food OR eating) AND TS=("social context*" OR "social determinant*" OR "social environment*" OR "food environment*" OR "social support" OR commensality OR "family meal*" OR "shared meal*") AND TS=(framework* OR model* OR guideline* OR assessment OR counseling OR counselling OR "care process")
```

## 5. Controlled vocabulary, field tags, filters

| Element | Current candidate | Reviewer attention |
|---|---|---|
| Controlled vocabulary | **None.** PubMed strings are `[Title/Abstract]` only; no MeSH, no publication types (e.g. Practice Guideline, Consensus Development Conference); LILACS strings use no DeCS. | P04 — decide whether MeSH/DeCS/Emtree-like layers are required per provider (open decision for Dr. Caio). |
| PubMed field tags | `[Title/Abstract]` on every term | Normative documents without abstracts are only reachable by title; the manuscript mentions a "rescue branch" for documents without abstracts that is **not** present in the Engine draft. |
| Wildcards inside phrases | `"dietary pattern*"`, `"position statement*"`, `"nutrition care model*"`, etc. | Current PubMed Help explicitly supports wildcards in phrase searches, including quoted phrases. This is not a syntax error by itself. However wildcards/field tags disable Automatic Term Mapping, so Search Details and controlled-vocabulary balance still require PRESS review. |
| Hyphenation | `food-based` unquoted | PubMed tokenisation; D01 technical run found 0 incremental records for `"food based"`. |
| Scopus | `TITLE-ABS-KEY(...) AND TITLE-ABS-KEY(...)` | Includes author keywords and indexer terms — field asymmetry vs PubMed `[tiab]` (open decision). |
| Web of Science | `TS=(...) AND TS=(...)` | Topic includes Keywords Plus — asymmetry vs PubMed. |
| LILACS/BVS | `tw:` fields, English terms only | No Portuguese/Spanish terms and no DeCS; likely poor fit for a Latin-American source. |
| SciELO | no field tags, English terms only | Same language concern. |
| Date limits | **None in the Engine draft.** Protocol/manuscript: B-NORM no lower limit; C-STRUCT from 2000-01 to the actual execution date. | P06 — must be written into the frozen strings, not left implicit. |
| Language limits | None at identification (protocol/manuscript). Inclusion requires an official version or verifiable translation in PT/EN/ES. | Consistent; confirm. |

## 6. Known items / sentinels

Engine set: 14 development sentinels, `docs/article1_closeout/ARTICLE1_KNOWN_ITEMS.md` (KI01–KI14, PMIDs recorded by the operator on 22/09; re-verify at provider).
Development snapshot: 11/14 retrieved by some route; 10/14 by the expected route. Diagnostic gaps: KI03 (eating competence), KI08 (LM professional competencies), KI10 (food environments), KI13 (Lifestyle Medicine and Healthy Nutrition, 2026).
The manuscript/protocol describe **16** sentinels — the two sets must be harmonised before PRESS (human decision).

## 7. Development evidence available to the reviewer (NOT PRISMA)

Technical PubMed run `article1_press_20260906T202201Z` (06/09/2026), `evidence/article1_press/…/TECHNICAL_SUMMARY.json`, status `TECHNICAL_DELTA_RUN_COMPLETE_HUMAN_REVIEW_PENDING`:

| Delta | Comparison | Baseline | Variant | Incremental | Human precision |
|---|---|---:|---:|---:|---|
| D01 | B-NORM + `food based` | 138,913 | 138,913 | 0 | not applicable (no increment) |
| D02 | B-NORM + `healthy eating` | 138,913 | 139,576 | 663 | 25-record sample, **pending** |
| D03 | C1 ± `meal plan*` | 4,053 | 4,586 | 533 | 25-record sample, **pending** |
| D04 | C3 standalone | — | 1,855 | 1,855 | 25-record sample, **pending** |
| D05 | C4 outside C1–C3 ∪ B-NORM | 143,873 | 149,928 | 6,055 | 25-record sample, **pending** |

These are PubMed hit counts from a development run. They are not screening results, not a corpus, and not PRISMA identification counts. The 100 sample records (D02–D05, 25 each) are the "d132-v1" packet; they carry a known recency bias from `rows[:limit]` sampling.

## 8. Provider audit

| PROVIDER | QUERY VERSION | NATIVE SYNTAX | VALIDATION STATUS | WHO VALIDATED | DATE | WARNINGS | NEXT ACTION |
|---|---|---|---|---|---|---|---|
| PubMed | article1-query-draft-v1 (compiled) | `[Title/Abstract]`, no MeSH | CANDIDATE_NOT_NATIVE_VALIDATED; delta routes executed technically (06/09); official syntax audit v0.2 completed | nobody (technical audit only) | 2026-09-28 | phrase wildcards are supported; field tags/wildcards disable ATM; no controlled vocabulary; no date limits; no no-abstract rescue | Run native Search Details on the chosen version; execute controlled-vocabulary rescue deltas; record warnings, counts, sentinels |
| LILACS/BVS | article1-query-draft-v1 (compiled) | `tw:` | BLOCKED | nobody | — | public interface HTTP 403 (D-130); English-only terms; no DeCS | Human decision on inclusion; if kept, auditable manual run on the official interface |
| SciELO | article1-query-draft-v1 (compiled) | untagged | BLOCKED | nobody | — | HTTP 403 (D-130); English-only | Same as LILACS |
| Scopus | article1-query-draft-v1 (compiled) | `TITLE-ABS-KEY` | EXTERNAL_VALIDATION_REQUIRED | nobody | — | simulation forbidden; field asymmetry | Licensed PILOT via institutional access after PRESS |
| Web of Science | article1-query-draft-v1 (compiled) | `TS=` | EXTERNAL_VALIDATION_REQUIRED | nobody | — | simulation forbidden; field asymmetry | Licensed PILOT via institutional access after PRESS |

Europe PMC, OpenAlex, Crossref, DOAJ and Semantic Scholar remain discovery/QA sources, not formal substitutes.

## 9. Specific questions for the PRESS reviewer

1. **P01:** Does the candidate B-NORM + C1–C4 architecture faithfully translate the approved canonical question, especially the transition from recommendation/dietary direction to prescription formats, competencies/repertoires, context/execution conditions, monitoring and continuity of care?
2. **P02:** Is `B-NORM ∪ C-STRUCT` the right top-level logic, or should C-STRUCT be constrained by a normative/document-type marker to stay within a documentary corpus?
3. **P02/P09:** C4 requires three blocks (anchor AND social context AND operational marker). Is `model*` / `framework*` / `assessment` an adequate operational marker, given D05's increment of 6,055?
4. **P03:** PubMed supports wildcards inside quoted phrases; does each wildcard phrase behave as intended in Search Details, and is loss of Automatic Term Mapping adequately compensated by explicit free-text/controlled-vocabulary branches?
5. **P04:** Test a controlled-vocabulary rescue layer before adoption: `Nutrition Policy`[MeSH]; `Diet`/`Diet, Healthy`[MeSH] combined with `Guideline`/`Practice Guideline`/`Consensus Statement` publication types and `Guidelines as Topic`/`Practice Guidelines as Topic`; for C1 test `Nutrition Therapy`[MeSH]. For LILACS/SciELO, decide DeCS + PT/ES terms if those providers remain formal.
6. **P05:** `counseling`/`counselling` are covered; are `diet*` vs `dietary` and `nutrition*` over-broad as anchors?
7. **P06:** Encode the date rules (B-NORM no lower limit; C-STRUCT 2000–) in each frozen string.
8. **P07:** Are KI13 and the social-context sentinels in scope? Which recall target is acceptable before freeze?
9. **P08/P09:** Should `standard*` (large exclusive share of B-NORM in the 22/09 development snapshot) be kept, restricted or tested for precision (S1)?
10. **P10:** Is `[tiab]` vs `TITLE-ABS-KEY` vs `TS` asymmetry acceptable, or should Scopus/WoS be restricted to title/abstract equivalents?

## 10. What this packet does not do

It does not record a reviewer, a PRESS decision, a C4 decision, GF-10 authorization, a query freeze, a formal search, eligibility decisions or PRISMA events.
