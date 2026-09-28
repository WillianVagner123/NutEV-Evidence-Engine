# Article 1 — PRESS Technical Audit v0.2

**Date:** 2026-09-28  
**Base:** `5adb56ccaf265b57b4085fdb3f960a371601fb58`  
**Nature:** technical pre-review support for the human PRESS reviewer.  
**Not a scientific gate:** this document does **not** set `PRESS=PASS`, authorize GF-10, freeze any provider query, execute a FORMAL search, emit PRISMA events, or make eligibility decisions.

## 1. Canonical question

> Como documentos normativos e estruturantes do cuidado alimentar de adultos formulam recomendações e direção dietética e em que medida as operacionalizam por meio de formas de prescrição, competências e repertórios, contexto, condições de execução, monitoramento e continuidade do cuidado?

Approved by Willian Vagner and supervisor Prof. Dr. Caio Eduardo G. Reis and synchronized in the active A1 artifacts.

## 2. PubMed syntax findings from current official NCBI documentation

### 2.1 Wildcards inside phrases are supported

Current PubMed Help explicitly supports wildcard searches in phrases, including quoted phrases such as `"breast feed*"` and phrases containing more than one wildcard. Therefore candidate terms such as `"dietary pattern*"[tiab]`, `"position statement*"[tiab]`, and `"nutrition care model*"[tiab]` are **not syntax errors merely because they combine quotes and an asterisk**.

What remains to be reviewed is semantic behavior in Search Details and recall/precision.

### 2.2 Field tags and wildcards disable Automatic Term Mapping

PubMed documents that search field tags restrict the search to the specified field and turn off Automatic Term Mapping. Wildcards also turn off Automatic Term Mapping. Therefore the current all-`[Title/Abstract]` strategy deliberately depends on explicit free-text coverage and does not automatically inherit MeSH expansion.

This makes P04 (controlled vocabulary/free-text balance) a substantive PRESS question rather than a syntax-cleanup issue.

### 2.3 Search Details still must be captured

The official PubMed Help states that Search Details show query interpretation and warnings. A formal native validation therefore still requires the chosen candidate strings to be run in PubMed/Advanced Search and the resulting Search Details, warnings, date, counts, and query identity to be recorded.

This audit does not claim that step has already occurred.

## 3. Controlled-vocabulary candidates identified in official MeSH

The following are technically valid concepts for **delta testing**, not automatic adoption.

### B-NORM candidates

- `Nutrition Policy[Mesh]`
  - MeSH entry terms include Nutrition Guidelines and Dietary Guidelines.
- `Diet[Mesh]`
  - entry terms include Dietary Pattern(s) and Food Pattern(s).
- `Diet, Healthy[Mesh]`
  - entry terms include Healthy Eating and Healthy Nutrition.
- `Guideline[Publication Type]`
- `Practice Guideline[Publication Type]`
- `Consensus Statement[Publication Type]`
- `Guidelines as Topic[Mesh]`
- `Practice Guidelines as Topic[Mesh]`

### C1 candidate

- `Nutrition Therapy[Mesh]`
  - entry terms include Medical Nutrition Therapy.
- `Patient Care Planning[Mesh]` is a possible broader care-structure concept but must be tested for noise before any adoption.

### C2 candidates

- `Professional Competence[Mesh]`
- `Health Literacy[Mesh]`

Both are broad and should only be tested inside a nutrition/food constrained branch. They must not be promoted merely because they exist in MeSH.

## 4. Proposed technical delta tests before human PRESS decision

These tests extend the existing D01–D05 development evidence. They remain PILOT/development and must not contribute to PRISMA.

### CV01 — B-NORM Nutrition Policy rescue

Compare current B-NORM with:

```text
current B-NORM
OR "Nutrition Policy"[Mesh]
```

Purpose: measure whether MeSH-indexed dietary/nutrition guideline records are missed by the all-`[tiab]` branch.

### CV02 — B-NORM controlled normative branch

Test the incremental yield of a constrained controlled-vocabulary branch:

```text
(
  ("Diet"[Mesh] OR "Diet, Healthy"[Mesh])
  AND
  (
    "Guideline"[Publication Type]
    OR "Practice Guideline"[Publication Type]
    OR "Consensus Statement"[Publication Type]
    OR "Guidelines as Topic"[Mesh]
    OR "Practice Guidelines as Topic"[Mesh]
  )
)
```

Purpose: evaluate a MeSH/PT rescue branch without making Lifestyle Medicine branding mandatory.

### CV03 — C1 Nutrition Therapy rescue

Test incremental yield from `"Nutrition Therapy"[Mesh]` inside the C1 architecture.

Purpose: recover MNT/nutrition-care material that may lack the current free-text phrases.

### CV04 — C2 controlled competence/literacy rescue

Within a nutrition/food-constrained branch, test `"Professional Competence"[Mesh]` and `"Health Literacy"[Mesh]` separately.

Purpose: diagnose KI08 and competency/literacy recall without importing generic competence/health-literacy literature.

### S01 — `standard*` marginal contribution

The development snapshot flagged a large exclusive contribution from `standard*`. Before retaining it in the frozen B-NORM string, isolate:

- total records unique to `standard*` relative to the other normative markers;
- a blinded relevance sample;
- document-family distribution;
- whether it contributes true normative/structuring documents or generic measurement/standards noise.

No retain/remove decision is made in this audit.

### C4 — social-context candidate

D05 produced 6,055 incremental PubMed records in the development run and its 25-record human precision sample remains pending. C4 cannot be adopted or rejected from count magnitude alone.

Required review:
- blinded precision sample;
- KI10 recovery;
- distinct contribution beyond B-NORM/C1–C3;
- whether the operational-marker block (`framework*`, `model*`, `guideline*`, `assessment`, `counseling/counselling`, `care process`) is too permissive.

## 5. Known-item diagnostics

Current development set: 14 items; 11/14 recovered by some route and 10/14 by the expected route.

Items requiring explicit pre-freeze review:

- **KI03 — Eating competence / Satter (PMID 17826695):** test `eating competence` as a C2 candidate; prior development snapshot reported low incremental cost (+115).
- **KI08 — Physician competencies for Lifestyle Medicine (PMID 20628134):** test a constrained professional-competence branch; do not make `physician competenc*` a universal term without precision review.
- **KI10 — INFORMAS food environments (PMID 24074207):** use as a C4 stress test; determine whether policy/monitoring language is needed.
- **KI13 — Lifestyle Medicine and Healthy Nutrition (PMID 42368033):** first adjudicate whether it is genuinely in scope; only then diagnose the missing retrieval concept.

The manuscript/protocol state 16 sentinels while the Engine has 14. The two absent identities are not inferable from current canonical evidence and must not be invented. Harmonization remains a human decision.

## 6. Provider implications

### PubMed

Current status remains `PENDING` / `CANDIDATE_NOT_NATIVE_VALIDATED`.

Technical syntax audit is complete, but native Search Details + counts + warning capture + controlled-vocabulary deltas are still required.

### LILACS/BVS and SciELO

No decision is made here on whether they remain formal providers. If retained, English-only free-text candidates are insufficiently justified for a Latin-American source; DeCS and Portuguese/Spanish terms require deliberate provider-native design and validation.

### Scopus and Web of Science

No simulation. Candidate translations must be run under licensed institutional access and checked for field asymmetry (`TITLE-ABS-KEY` and `TS` versus PubMed `[tiab]`).

## 7. PRESS questions after this technical audit

P01. Does B-NORM + C1–C4 faithfully translate the approved canonical question?  
P02. Is the top-level union logic appropriate for a documentary corpus?  
P03. Do wildcard phrases and field tags behave as intended in PubMed Search Details?  
P04. Which controlled-vocabulary rescue branches improve recall enough to justify adoption?  
P05. Which spelling/phrase variants remain necessary after native validation?  
P06. Are route-specific date rules correctly encoded at freeze?  
P07. Is known-item recovery satisfactory, and how should the 14-versus-16 sentinel discrepancy be resolved?  
P08. Which optional terms/branches have acceptable incremental yield?  
P09. What does blinded human relevance review show for D02–D05, S01 and any new controlled-vocabulary deltas?  
P10. Are cross-database translations faithful despite field/indexing differences?

## 8. Official sources consulted

- PubMed Help — searching phrases, wildcards/truncation, field tags, Search Details: https://pubmed.ncbi.nlm.nih.gov/help/
- MeSH: Nutrition Policy: https://www.ncbi.nlm.nih.gov/mesh/68018673
- MeSH: Diet: https://www.ncbi.nlm.nih.gov/mesh/68004032
- MeSH: Diet, Healthy: https://www.ncbi.nlm.nih.gov/mesh/2016583
- MeSH: Guidelines as Topic: https://www.ncbi.nlm.nih.gov/mesh/68017408
- MeSH: Practice Guidelines as Topic: https://www.ncbi.nlm.nih.gov/mesh/68017410
- MeSH: Guideline [Publication Type]: https://www.ncbi.nlm.nih.gov/mesh/68016431
- MeSH: Practice Guideline [Publication Type]: https://www.ncbi.nlm.nih.gov/mesh/68017065
- MeSH: Consensus Statement [Publication Type]: https://www.ncbi.nlm.nih.gov/mesh/68016446
- MeSH: Nutrition Therapy: https://www.ncbi.nlm.nih.gov/mesh/68044623
- MeSH: Professional Competence: https://www.ncbi.nlm.nih.gov/mesh/68011361
- MeSH: Health Literacy: https://www.ncbi.nlm.nih.gov/mesh/68057220

## 9. Gate state after this audit

```text
PRESS                          = PENDING
PRESS_REVIEWER                 = HUMAN_DECISION_REQUIRED
PUBMED_NATIVE_VALIDATION       = PENDING
C4                             = PRESS_ONLY_CANDIDATE_NOT_APPROVED
GF-10                           = false
QUERY_FREEZE                    = false
FORMAL_PROVIDER_SEARCH_EXECUTED = false
PRISMA_SEARCH_EVENT_EMITTED     = false
```

No state above is promoted by this technical audit.
