# Scientific visual flow

The NutEV visual flow connects three existing surfaces without creating a new scientific state machine:

1. **Evidence Map** — structural navigation over the verified rank-blind corpus.
2. **Scientific Intelligence** — inspection of domain structure, result-bundle availability and source-linked finding candidates.
3. **Human Review** — authenticated, application-scoped human decisions governed by the existing Review runtime.

## Interaction contract

The shared `scientific-flow.js` / `scientific-flow.css` layer is presentation and navigation only.

- Evidence Map may pass the selected **domain** to Scientific Intelligence through the URL.
- Scientific Intelligence hydrates that domain through its existing domain selector and existing `change` event contract.
- The visual domain landscape is derived from already-rendered domain cards and delegates clicks back to the existing `data-select-domain` controls.
- Human Review progress is derived from the already-rendered assignment state. The shared visual layer performs no API request and writes no Review decision.
- No map or intelligence filter is imported into Review as a decision, eligibility signal, inclusion status, EvidenceClaim, certainty assessment or PRISMA event.

## Interpretation guardrails

The visual layer must preserve these distinctions:

- document volume != evidence strength or certainty;
- result-bundle coverage != accepted EvidenceClaim;
- recurring labels != consensus;
- sparse mapping != evidence gap;
- navigation route != inclusion;
- Review progress != inclusion rate or scientific result;
- entering Human Review does not transfer a visual filter into a human decision.

## Accessibility and responsive behavior

The flow uses native links and buttons, visible numeric labels, keyboard focus states and responsive layouts. The Review progress indicator exposes `role="progressbar"` with current and maximum values.

## Ownership of scientific state

Scientific state remains owned by the existing systems:

- Evidence Map and Scientific Intelligence remain rank-blind structural/read-only surfaces.
- Human Review remains isolated by workspace, project and `ResearchApplication` on the server side.
- PRESS, GF-10, EvidenceClaim promotion, eligibility, inclusion and PRISMA remain outside this visual integration layer.
