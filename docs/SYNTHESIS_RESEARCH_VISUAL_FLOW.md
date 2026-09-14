# Synthesis Research Visual Flow

This document defines the shared visual-navigation layer across:

```text
Human Synthesis Review
  -> Human Synthesis Brief
  -> Ask NutEV
```

The sequence is a **research-workspace navigation flow**, not a scientific-promotion pipeline.

## Core rule

The shared `synthesis-flow.js` layer may read already-rendered browser state and invoke existing local controls. It must not create a second scientific state model.

The layer therefore does not:

- fetch Article 1 data itself;
- POST scientific decisions;
- persist review judgments;
- import/export Review or Brief artifacts automatically;
- create EvidenceClaims;
- alter eligibility, inclusion, RoB or certainty;
- authorize PRESS, GF-10, query freeze or PRISMA;
- call an external LLM.

## Stage 1 — Human Synthesis Review

The flow rail reports operational state already present on `/synthesis-review.html`:

- declared reviewer name;
- current anchor-comparison progress;
- local Review ledger size;
- current Review health text.

The visual action `Exportar revisão` delegates to the existing `#exportReview` control.

This does not bypass the Review export contract. Reviewer identity, explicit human relation labels, rationale, context fingerprint and other existing fail-closed checks remain authoritative.

The exported artifact remains:

```text
NUTEV_HUMAN_SYNTHESIS_REVIEW_DRAFT_V1
canonical: false
```

Opening the Brief does not transfer browser-local decisions. The researcher must export the Review artifact and explicitly import it into the Brief.

## Stage 2 — Human Synthesis Brief

The flow rail reports:

- current Brief health;
- pass/fail verification-item counts already rendered by the Brief;
- human-decision count after successful rendering;
- verified/noncanonical semantics.

The Brief remains blocked until its existing checks succeed, including source type, noncanonical semantics, content SHA-256 and current context fingerprint.

Navigation from Brief to Ask does **not** pass:

- relation labels;
- reviewer rationale;
- source-review content SHA;
- Brief SHA;
- pairwise decisions;
- descriptive relationship counts.

The Brief remains a presentation/export artifact, not an input promoted into Ask as accepted evidence.

## Stage 3 — Ask NutEV

The flow rail reports operational state already rendered by `/ask.html`:

- Article 1 safe-context availability;
- current retrieval result metadata;
- selected supporting-document count;
- whether a grounded context packet has been materialized.

`Gerar contexto grounded` delegates to the existing `#buildPacket` control.

Ask NutEV continues to read the verified rank-blind Article 1 bundle through its existing implementation. The shared visual layer does not fetch that bundle and does not import Human Synthesis Review or Brief artifacts.

Therefore:

```text
Review judgment != Ask evidence
Brief verification != Ask evidence
retrieval match != eligibility
retrieval match != scientific relevance validation
context packet != canonical synthesis
```

## Navigation implementation

The current stage is rendered as a non-link element with `aria-current="step"`.

Other stages use native buttons that call `location.assign(...)`. This avoids introducing extra canonical `<a href>` selectors into pages that already have navigation and E2E contracts around their existing links.

## Accessibility and responsiveness

The visual flow uses:

- native buttons for interactive controls;
- `:focus-visible` states;
- responsive single-column layouts below 900 px;
- full-width actions on narrow mobile layouts.

## Scientific interpretation boundary

The flow intentionally exposes **operational readiness**, not scientific quality.

Counts such as reviewed pairs, verification passes, retrieval results or selected documents are descriptive UI state only. They must never be converted into:

- evidence-strength scores;
- certainty scores;
- automated convergence/contradiction judgments;
- recommendation strength;
- study eligibility;
- PRISMA progress.
