# Evidence interpretation visuals

The Evidence Map, Scientific Intelligence and generic Human Review surfaces share a visual navigation layer with three stages:

1. **Structure — Evidence Map**
2. **Inspect — Scientific Intelligence**
3. **Human review — Review Control**

This is a navigation and comprehension aid only. It is not a scientific state machine and does not move evidence automatically between stages.

## Data ownership

`apps/nutev-web/evidence-interpretation.js` performs no scientific fetches and creates no alternate persistence model. It derives its visuals from DOM already rendered by the authoritative page modules and delegates interactions back to existing controls.

- Evidence Map bars are derived from the rendered domain × document matrix and delegate domain selection to `#mapDomainFilter`.
- Scientific Intelligence bars are derived from the rendered domain synthesis cards and delegate selection to the existing `data-select-domain` controls.
- Human Review progress is derived from rounds already returned by the authenticated Review surface. Clicking a visual round delegates to the existing open/refresh action; the visual module cannot create rounds, save decisions or submit a review.

## Scientific boundaries

### Evidence Map

A concentration bar is structural document placement. It does **not** represent evidence strength, certainty, methodological quality, absence of literature or an evidence gap. A reference may map to more than one operational domain.

### Scientific Intelligence

`finding-ready` means that a result bundle is technically materialized for inspection. It does **not** mean that a finding is accepted, convergent, eligible, certain or an EvidenceClaim.

### Human Review

The progress bar measures only how many configured reviewers have submitted and locked their own assessment. It does **not** calculate inclusion, agreement, adjudication, risk of bias, certainty, recommendation strength or PRISMA counts.

## Interaction and accessibility

The visual controls are native buttons or links, expose active state through `aria-pressed` / `aria-current`, preserve keyboard focus states and collapse to a single-column layout on smaller screens.

## Isolation guarantees

The visual layer does not:

- call Review POST endpoints;
- infer a legacy round binding;
- transfer a decision between projects or ResearchApplications;
- generate evidence quality scores;
- convert recurrence into consensus;
- convert sparse mapping into an evidence gap;
- alter PRESS, GF-10, Review, EvidenceClaim, Recommendation or PRISMA state.
