# Data Governance

Rules for what data may and may not enter this repository, and how data is
handled by the pipeline.

## Never commit

- Personal data (names, emails, identifiers) of real people.
- Patient or research-participant data of any kind.
- Copyright-protected full texts or protected PDFs (see
  `docs/COPYRIGHT_AND_FULL_TEXT_POLICY.md`).
- Secrets: API keys, tokens, `.env` files, private keys, passwords.
- Signed URLs, cookies, or credential-bearing logs.
- Raw webhook payloads, real run outputs, or local databases.

These are enforced by `.gitignore`, workflow guards, and the security scan
(gitleaks) added in CI.

## Allowed in the repository

- Synthetic/demo data (clearly labeled as demo; **not** evidence).
- Public metadata: DOI, official URLs, titles, authors, dates.
- Minimum permitted excerpts (see copyright policy).
- NutEV configuration (rules, ontology, scoring, taxonomy).
- Sanitized, derived tables and reports that contain no protected/private content.

## Data classes handled by the pipeline

| Class | Example | Storage | May be committed? |
|---|---|---|---|
| Metadata | DOI, URL, title | `02_metadata/` | Yes (public metadata) |
| Public download | open-access record | `03_corpus/03B_public_downloads/` | No (runtime only) |
| Official doc | official guideline capture | `03_corpus/03C_official_docs/` | No (runtime only) |
| Derived table | scored matrices | `06_tables/` | Only if sanitized + non-protected |
| Logs | run logs | `07_logs/` | Only sanitized (no URLs w/ tokens) |
| Demo | synthetic | any (demo project root) | Yes, labeled as demo |

Runtime output directories (`project_output*/`) are git-ignored.

## Handling personal/clinical data

The system is **not** a store for personal or clinical data. If such data is
needed for a study, it must live in an appropriate, access-controlled system
outside this repository, governed by the relevant ethics approval and data
protection rules. Do not stage it here, not even temporarily.

## Artifact governance in CI

Workflows must upload only metadata, sanitized logs, derived tables and permitted
reports — never raw captures, full PDFs/HTML, or unsanitized webhook payloads. See
the workflow-hardening notes and each workflow's upload manifest.

## Incident handling

If protected or personal data is committed by mistake:
1. Do not just delete in a new commit (history retains it).
2. Report privately (see `SECURITY.md`).
3. Coordinate history remediation with maintainers as a separate, explicit action
   (out of scope for routine PRs).
