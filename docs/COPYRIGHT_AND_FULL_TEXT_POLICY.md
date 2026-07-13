# Copyright and Full-Text Policy

NutEV/NutMEV analyzes the scientific and official literature. It must do so
without redistributing copyright-protected content.

## Core rule

**Do not redistribute protected full texts or protected PDFs.** The repository,
its examples, and its CI artifacts must not contain third-party full-text
documents unless their license explicitly permits redistribution.

## What we share instead

For every source, prefer sharing, in this order:

1. **DOI** and/or the **official URL**.
2. **Bibliographic metadata** (title, authors, venue, date, identifiers).
3. **The minimum permitted excerpt** needed to support a specific claim (short
   quotation with precise locator), consistent with fair use / fair dealing and
   the source license.

## Full text at runtime

- The pipeline may fetch and process documents **locally at runtime** (into
  git-ignored `project_output*/03_corpus/`), but those captures are **not**
  committed and **not** uploaded as raw CI artifacts.
- Derived, non-infringing outputs (scores, structured claims with locators,
  summaries authored by the project) may be shared.

## Official / open documents

Official guidelines and open-access documents may still carry usage terms. Verify
the license before including any excerpt beyond the minimum, and always attribute
the source.

## Examples directory

`examples/` must contain only synthetic data, public metadata, or content the
project is licensed to share. No third-party PDFs. Generated sample reports whose
source provenance is unclear should be reviewed and removed if they embed
protected text (see `docs/PUBLIC_RELEASE_AUDIT.md` §8).

## If in doubt

Treat the item as protected. Share the reference, not the text. Log any unresolved
licensing question as a pending item rather than committing the content.
