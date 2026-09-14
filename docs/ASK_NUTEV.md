# Consulta de Evidências — contrato funcional

> Compatibility note: the historical filename `ASK_NUTEV.md` remains stable for links and tooling. The product surface is **Consulta de Evidências / Evidence Query**, not “Ask NutEV”.

`/ask.html` is the NutEV query surface for the verified Article 1 corpus. It performs deterministic matching and composes an auditable **Evidence Packet / Pacote de Evidências**. It is not a chat surface and it does not make scientific decisions.

## Source

The page reads only the verified, rank-blind compatibility bundle at `agent-context/article1/ARTICLE_SUMMARIES.jsonl`. In product language this is part of the **Evidence Context / Contexto de Evidências** layer.

The bundle contains safe metadata, route membership and deterministic review-profile context. It does not contain protected full text, Bank rank/score/tier or machine-relevance scores.

## What the system does

1. accepts a natural-language research question;
2. tokenizes it locally and performs deterministic lexical matching over titles, citation stubs, document class, route membership, operational domains and matched terms already present in the safe review profile;
3. shows supporting documents and explains why they matched;
4. allows the researcher to select a smaller supporting set;
5. generates an auditable Evidence Packet with question, scope, supporting document IDs and verified context references;
6. points back to the Corpus / Scientific Dossier for deeper inspection.

The matching score is an internal navigation heuristic. It is not displayed or interpreted as scientific relevance, quality, certainty, eligibility or recommendation.

## Scientific boundary

Consulta de Evidências must never turn any of the following into a scientific decision:

- lexical match;
- route membership;
- document-class profile;
- retrieval/full-text status;
- evidence-excerpt count;
- result-bundle count.

The surface does not include/exclude studies, assign risk of bias or certainty, approve recommendations, authorize PRESS/GF-10/query freeze, or emit PRISMA events.

## System boundary

The current implementation is deterministic and does not require an external model endpoint to search the verified corpus or build the Evidence Packet.

The packet is a portable, auditable system artifact. If downstream analytical tooling consumes it, that tooling must preserve the same scientific boundaries and must not silently transmit protected full text or promote automated output into accepted scientific evidence.

## Performance

Client-side matching is bounded to the verified Tier A context materialized for the current project. Production totals are runtime data and must not be hardcoded into this contract. This surface must not be changed to download the entire Bank corpus to the browser.
