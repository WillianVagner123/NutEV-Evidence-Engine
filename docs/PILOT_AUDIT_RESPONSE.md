# Pilot Audit — Response and Status

Response to the technical/scientific audit of the v0 pilot run (busca1 only).
Findings are mapped to concrete actions. "Fixed" = code change landed with tests;
"Config/tuning" = needs rule/keyword curation; "Data" = needs human-curated
sources; "By design" = intended, only labeling/communication adjusted.

| # | Finding | Status | Action |
|---|---|---|---|
| 1a | Dashboard shows 0 extracted texts | **Fixed** | `run_summary` now records real `extracted_texts` from the extraction manifest (was falling back to `ocr_docs`≈0); dashboard counts `ok/ok_ocr/fake_pdf_*`. |
| 1b | Manifest accepts junk ("Redirecting", "Checking your browser", reCAPTCHA) as valid | **Fixed** | Extractor rejects anti-bot/redirect/too-thin pages → new statuses `junk_or_blocked` / `too_short`; junk text no longer reaches the classifier or claim extractor. |
| 2 | Search too broad (pharmacology, oncology VTE, pediatrics, off-scope) | **Fixed** | Scope gate tags every record: `dietary_centrality`, `scope_status` (in_scope / off_scope_review / low_dietary_signal), `scope_flags` (pharmacology, oncology_vte, pediatric_only, surgical) so reviewers can exclude off-scope material. |
| 3 | Only 12 official sources | **Fixed** | Global per-country manifest (`official_sources_countries.json`, ~51 countries / 72 official sources) merged into busca1. URLs flagged `verify:true` need human verification before the definitive run. |
| 4 | Dietary patterns barely classified (918/967 none) | **Fixed (partial)** | Pattern detection rewritten with synonyms + word boundaries (MedDiet, DASH full name, Nordic, MIND, portfolio, intermittent fasting, paleo, pescatarian…; `dash` no longer matches "dashboard"). Remaining gap is corpus specificity (#2). |
| 5 | Claims are not confirmed evidence (`inference_only`, empty quotes; "supported" overstated) | **Fixed** | "supported" now requires a **substantial verbatim quote (≥40 chars)** from genuinely-extracted text; else `inference_only`. Summary adds `evidence_claims_inference_only`. Docs clarify "supported" = quote-backed, **not** validated. |
| 6 | The 5 candidates are review queues, not recommendations | **By design** | Governance already states these are `RecommendationCandidate`s for human review, not final recommendations. No inflation of claims/candidates as findings. |
| 7 | Version/duplication (GLP-1 parallel pubs; annual Standards of Care) | **Fixed** | Documents are grouped into version families and tagged `document_relation`: standalone / primary_version / annual_version / parallel_publication / guideline_chapter / supplement. New `NUTEV_VERSION_FAMILIES.csv` + QA sheet. |
| 8 | Priority texts blocked (403: Diabetes Journals, OUP, Wiley, MDPI, LWW, NEJM) | **Fixed (OA fallback)** | Legal open-access copies (PMC from pmcid, OpenAlex/Unpaywall OA URL) are tried **before** the blocked publisher landing; still never bypasses a paywall. |

## What the pilot demonstrated (for the qualification)

- Technical viability of the engine (search, orchestration, file organization).
- Retrieved and organized 967 unique records with resilient partial export.
- Surfaced access limitations to full texts and the need to restrict scope.
- Exposed the extraction-counting and false-positive bugs (now fixed).
- Produced artifacts for human triage and review.

**Not** to be presented as findings: the raw claims and the 5 candidates are
exploratory review material, not validated scientific results.

## Next correct run — controlled pilot (20–30 pre-confirmed documents)

As proposed, the next round should be a **controlled pilot** with a small,
pre-confirmed corpus, separating official dietary guides from clinical
nutrition guidelines:

1. Curate 20–30 documents by hand (DOIs / official URLs), split into:
   - **guias alimentares oficiais** (busca1) — e.g. FAO/WHO + national bodies;
   - **diretrizes clínicas nutricionais** (busca2a).
2. Put them in a fixed input list (metadata only; no third-party PDFs committed).
3. Run extraction + claims on that curated set and inspect:
   - extracted-text quality (no `junk_or_blocked`);
   - dietary-pattern classification coverage;
   - quote-backed vs inference-only claim ratio.
4. Only then widen the search, with the scope/exclusion tuning (#2) and the
   country/region official-source manifest (#3) in place.

## Proposed next PRs (need your input where marked)

- `feat(search): diet-centrality gate + off-scope exclusion terms` (#2).
- `feat(sources): official manifest by country/region/institution` (#3 — **which
  countries/bodies?**).
- `feat(dedup): distinguish annual versions / parallel publications` (#7).
- `feat(download): resolve open-access copies before giving up` (#8).
