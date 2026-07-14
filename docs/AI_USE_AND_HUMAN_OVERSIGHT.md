# AI Use and Human Oversight

NutEV/NutMEV can use Large Language Models (LLMs) as **assistants**. This document
states exactly what AI may and may not do, and where humans are required.

## What AI may do

- Help organize, cluster and classify retrieved records.
- Help extract structured fields from documents (with source locators).
- Draft summaries and candidate wording for human review.
- Suggest search terms / query expansion.

## What AI may NOT do

- **Define final approval** of a recommendation. Approval is a human act.
- Invent citations, DOIs, quotes, or source locations.
- Resolve conflicting evidence silently.
- Turn a `RecommendationCandidate` into a final clinical recommendation.
- Access or emit personal/clinical data.

## Human-in-the-loop guarantees

1. Every recommendation reaching "final" status passed a human review step.
2. Every AI-assisted claim is traceable to a document + location and is
   re-checkable by a human.
3. Reviewers can see, and must be able to override, any AI-produced field.
4. Conflicts and low-confidence items are routed to the human-review queue
   (`NUTEV_HUMAN_REVIEW_QUEUE`, `NUTEV_ADJUDICATION_QUEUE`), never auto-resolved.

## Running without any LLM

NutEV runs fully without an LLM. The engine currently ships with **no built-in
LLM integration** (the optional LLM scaffolding was removed from the tree);
`--llm-enabled` stays off, deterministic rules and human review are the only
decision paths, and no paid API is required for the pipeline or the demo.

## Provider configuration

- The engine does not call any LLM. If LLM assistance is reintroduced in the
  future it must remain optional and assistive only (never approving a
  recommendation).
- API keys, when used by external tooling, are read from environment variables
  and never committed.
- The default PR CI never calls a paid/hosted LLM.

## Auditability

AI-assisted decisions are logged with enough context (inputs, model role, source
locators) for a human to reconstruct and challenge them. See
`docs/NUTEV_AUDIT_ENGINE.md` and `docs/SCIENTIFIC_GOVERNANCE.md`.
