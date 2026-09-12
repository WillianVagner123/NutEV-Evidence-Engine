# NutEV Web

The repository contains **two web runtimes with different trust boundaries**. Do not treat them as interchangeable.

## 1. Hosted product runtime — supported production product

This is the user-facing NutEV 1.1.0 platform deployed behind the production HTTPS/authentication layer.

Primary characteristics:

- authenticated multi-tenant sessions;
- explicit workspace, project and ResearchApplication context;
- Search, Library, Exports and persisted search history scoped to the authorized context;
- project/application configuration through the product UI;
- backend authorization revalidated per private operation;
- production deployment through the exact-SHA release barrier.

Ordinary hosted users should use the deployed HTTPS product, currently configured by operations at:

```text
https://nutev.mindsperformance.com.br
```

The hosted product server implementation is `secure_server.py`. Do **not** replace the production entrypoint with the local scientific server described below.

## 2. Local scientific / validation runtime — workstation or institutional LAN

`server.py` is a local scientific interface used for reference discovery, scientific dashboards and the controlled validation workflow. It is intended for localhost or a trusted institutional LAN, not as the public multi-tenant product.

Start locally from the repository root:

```bash
python apps/nutev-web/server.py
```

Default address:

```text
http://127.0.0.1:8765/
```

For assessor links on the same trusted LAN:

```bash
python apps/nutev-web/server.py --host 0.0.0.0
```

> **Security boundary:** do not expose this local HTTP server directly to the public internet. Remote/public use requires an institution-managed HTTPS/authentication layer. The hosted multi-tenant runtime remains the supported public product surface.

The validation coordinator endpoints remain local-machine restricted. Assessor links use individual tokens in the URL fragment; do not send both assessor links to the same person.

## Shared scientific contracts

Both runtimes must preserve the same product/scientific boundaries:

- rankings are **reading/retrieval priority**, not methodological quality, certainty or clinical recommendation;
- unavailable providers are reported as unavailable/failed, never silently converted to zero literature;
- Scopus/Web of Science are not simulated without licensed access;
- identifiers and references are not invented to make records pass guardrails;
- provenance, deduplication identity and project/private state remain explicit;
- software/CI success does not imply scientific validation.

The current general scientific verdict is `B — DEMOTE` until an independent benchmark demonstrates incremental benefit.

## Hosted product journey

The supported product mental model is:

```text
LOGIN
  -> WORKSPACE
  -> PROJECT
  -> RESEARCH APPLICATION
  -> SEARCH
  -> LIBRARY
  -> REVIEW / SPECIALIZED SCIENTIFIC TOOLS WHEN APPLICABLE
  -> EXPORT
```

A project may initially have no ResearchApplication. The product UI must then offer the supported templates and configure the selected application before presenting it as a ready research context.

The generic primary navigation intentionally does not expose the current Article-1-specific `/review.html` as a universal Review surface. Specialized review/scientific routes remain under advanced tooling until a generic ResearchApplication-scoped review surface exists.

## Search behavior

The engine can query supported providers such as PubMed, Europe PMC, OpenAlex, Crossref, DOAJ, Semantic Scholar and the configured Latin-American routes. Completed runs are persisted; transient progressive-job state may be lost on process restart, but completed engine runs remain available.

Canonical identity/deduplication follows the product contract implemented by the engine. Provider failures and credential-dependent providers remain explicit in run evidence.

## Scientific validation workflow

The local `/validation/` flow remains fail-closed:

1. prepare a frozen round;
2. collect independent assessor decisions;
3. adjudicate only human disagreements;
4. build and validate the gold-standard ledger;
5. compute validation metrics only after the gold gate;
6. lock the validation decision;
7. keep the external test sealed until the protocol permits opening it.

A gold-process PASS means the process artifacts are complete/coherent; it does **not** mean NutEV performance is scientifically superior.

## Documentation

Current product documentation is indexed at [`../../docs/README.md`](../../docs/README.md).

Important references:

- [`../../docs/ARCHITECTURE.md`](../../docs/ARCHITECTURE.md)
- [`../../docs/AUDITABILITY_AND_GUARDRAILS.md`](../../docs/AUDITABILITY_AND_GUARDRAILS.md)
- [`../../docs/SEARCH_PROVIDERS.md`](../../docs/SEARCH_PROVIDERS.md)
- [`../../docs/KNOWN_LIMITATIONS.md`](../../docs/KNOWN_LIMITATIONS.md)
- [`../../docs/PRODUCTION_USABILITY_AUDIT.md`](../../docs/PRODUCTION_USABILITY_AUDIT.md)
- [`../../validation/SCIENTIFIC_VALIDATION_STATUS.md`](../../validation/SCIENTIFIC_VALIDATION_STATUS.md)

Historical sprint/release-closeout reports are kept under `docs/archive/` and are not current product contracts.