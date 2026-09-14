# Bilingual interface — PT-BR / EN

The NutEV web interface supports a presentation-language preference without changing scientific state, evidence objects, eligibility, Review decisions or release gates.

## Default and selector

- **Português (Brasil)** is the default language.
- The interface exposes a native **PT / EN** switch.
- The explicit choice is stored only as the UI preference `nutev_language` in `localStorage`.
- `?lang=pt-BR` and `?lang=en` may initialize the interface language for a page visit.
- `<html lang>` is updated to `pt-BR` or `en` for accessibility and browser semantics.

## Runtime coverage

`apps/nutev-web/i18n.js` is bootstrapped from presentation-layer modules rather than from authentication/session code or a parallel application shell:

- `product-ui.js` — shared authenticated product presentation layer;
- `login.js` — login presentation layer;
- `scientific-flow.js` — Evidence Map, Scientific Intelligence and Human Review;
- `operational-cycle.js` — Evidence Radar, Strategy Lab and Quality Observatory;
- `synthesis-flow.js` — Synthesis Review, Synthesis Brief and Ask NutEV;
- `dashboard-visual.js` — advanced scientific dashboard;
- `evidence.js` — Evidence Explorer;
- `review-routes.js` — Review Routes;
- `strategy-flow-sync.js` — QA, PRESS and regional-route review surfaces.

`tenant-session.js` intentionally contains **no i18n bootstrap**. Presentation-language loading is kept outside the browser context lease so language choice cannot participate in session/context invalidation or authorization behavior.

The translation observer also handles known UI inserted after page load.

## Portuguese cleanup

The PT-BR registry normalizes mixed legacy UI such as `provider`, `workspace`, `retrieval grounded`, `result bundle`, `finding-ready`, `rank-blind`, `Watch`, `Query freeze`, `full text`, `fail-closed` and similar presentation language into Portuguese equivalents.

The registry supports aliases so an old mixed string can be rendered as clean Portuguese by default and as coherent English when EN is selected, without rewriting the underlying scientific object.

## Protected scientific content

The translator is intentionally presentation-only. It does not translate source/scientific content inside protected selectors, including article titles, abstracts, finding excerpts, raw enums, block quotes and citations.

Canonical technical identifiers and scientific acronyms remain stable where they are part of the scientific contract, including examples such as:

- PRESS;
- GF-10;
- PRISMA;
- B-NORM;
- C-STRUCT;
- EvidenceClaim when used as the canonical object name.

## Scientific boundary

The language module:

- performs no scientific `fetch`;
- performs no `POST` or backend mutation;
- creates no Review, eligibility, inclusion, risk-of-bias, certainty, recommendation or PRISMA state;
- does not alter ranking, provider results, search strategy or evidence artifacts;
- persists only the local presentation-language preference.

Changing PT/EN therefore changes **copy and accessibility semantics only**. It does not change NutEV scientific interpretation or validation status.

## Maintenance rule

New interface copy should be added to the bilingual registry when a new product surface is introduced. Scientific source text should not be added to the registry merely to make it visually uniform; source language remains part of the evidence/provenance context.
