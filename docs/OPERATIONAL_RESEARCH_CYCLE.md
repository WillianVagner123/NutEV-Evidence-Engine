# Operational Research Cycle

This document defines the shared visual-navigation layer across:

```text
Evidence Radar
  -> Strategy Lab
  -> Quality Observatory
```

The sequence is an **operational research cycle**, not a scientific-promotion pipeline.

## Core rule

The shared `operational-cycle.js` layer may read browser state already rendered by each page and invoke existing local controls. It must not create a second scientific state model.

The layer therefore does not:

- fetch Article 1 data itself;
- POST scientific decisions;
- persist strategy or quality state;
- convert Radar gaps into search terms;
- approve PRESS;
- authorize GF-10;
- freeze a query;
- execute a formal provider search;
- create eligibility, inclusion, RoB, certainty, EvidenceClaim, recommendation or PRISMA state;
- convert operational quality metrics into evidence-quality scores.

## Stage 1 — Evidence Radar / Observe

The shared rail reports operational state already rendered by `/radar.html`:

- Radar engine health;
- topics with technical gaps;
- units requiring active search;
- observed provider count;
- current Watch state.

The visual actions `Atualizar Radar` and `Ver Watch` delegate to the existing `#refreshRadar` and `#jumpChanges` controls.

The following semantics remain explicit:

```text
priority != evidence grade
gap != exclusion
provider unavailable != literature absent
Watch change != scientific conclusion
```

Opening Strategy Lab does not transfer Radar counts, priorities, flags or events into vocabulary decisions.

## Stage 2 — Strategy Lab / Prepare

The rail reports values already rendered by the canonical pre-PRESS workspace:

- PRESS status;
- GF-10 authorization state;
- query-freeze state;
- formal-search execution state;
- number of visible PRESS delta-test candidates.

Those values are reflected, never inferred by the shared layer.

Navigation buttons may open QA and PRESS, but the visual cycle cannot:

- mark PRESS as PASS;
- unlock GF-10;
- approve candidate terms;
- promote disease or study-design terms from frequency;
- execute formal search;
- emit PRISMA.

Therefore:

```text
Radar frequency != vocabulary inclusion
Strategy loaded != Strategy approved
PRESS candidate != PRESS PASS
GF-10 displayed != GF-10 authorized by the visual layer
```

## Stage 3 — Quality Observatory / Verify

The rail reports operational observability already rendered by `/quality.html`:

- full-text technical coverage;
- context age;
- unclassified-document count;
- visible operational errors and attention states;
- overall Observatory health text.

`Atualizar Observatory` delegates to the existing `#refreshQuality` control.

Quality Observatory remains explicitly about system quality:

```text
system health != methodological quality
retrieval coverage != screening
metadata completeness != certainty
provider error != evidence absence
zero operational errors != scientific validation
```

It does not authorize Strategy and does not act as a scientific gate.

## Cycle semantics

`Observe -> Prepare -> Verify` is deliberately a navigational mental model:

- **Observe** the current operational evidence environment.
- **Prepare** explicit pre-PRESS strategy decisions.
- **Verify** system integrity and technical completeness.

The cycle may be traversed in any direction. No stage automatically advances another stage.

## Implementation boundary

`operational-cycle.js`:

- contains no `fetch(...)`;
- contains no XHR;
- contains no POST;
- contains no scientific persistence;
- reads only rendered DOM state;
- invokes only existing refresh/watch controls or `location.assign(...)` navigation.

The current stage is rendered as a non-link element with `aria-current="step"`. Other stages use native buttons to avoid adding duplicate canonical anchors that could interfere with existing browser tests.

## Accessibility and responsiveness

The cycle uses:

- native buttons;
- visible `:focus-visible` states;
- responsive single-column stage/metric layouts below 900 px;
- full-width actions on narrow mobile layouts.

## Scientific interpretation boundary

All counts and statuses shown by this cycle are operational descriptors only. They must never be transformed into:

- evidence-strength scores;
- certainty scores;
- automated inclusion decisions;
- automated vocabulary approval;
- recommendation strength;
- scientific validation status;
- PRISMA progress.
