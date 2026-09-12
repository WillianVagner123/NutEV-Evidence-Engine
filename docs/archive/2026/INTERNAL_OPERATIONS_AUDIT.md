# Internal operations audit — Sprint 15

Goal: support the NutEV as an operated research platform without requiring routine SQLite edits or access to private scientific payloads.

## Operator questions that must be answerable

1. Is production healthy, which commit/version is running and is auth `pilot`?
2. Is the account active and does it have a workspace membership?
3. Does the selected workspace contain an accessible project?
4. Does the project have an application/template and what is its operational status?
5. Are providers configured, skipped, partial or failed?
6. Is a search persisted or only an in-memory job?
7. Is a review assignment pending/submitted/locked?
8. Does an export exist and is its audit chain valid?
9. Is a thesis-specific gate technical, scientific or provenance-blocked?

## Current operating model

Identity provisioning remains an explicit operator action using `tools/provision_nutev_user.py`; plaintext passwords are prompted interactively and are never CLI arguments. Workspace/project access is server-authoritative. PLATFORM_ADMIN is infrastructure authority, not implicit scientific read access.

## Sprint action

Add public-safe, read-only runtime diagnostics before adding an admin UI. A support diagnostic may expose counts/status/fingerprints but must not print passwords, tokens, queries, abstracts/full text, project names or raw private tenant IDs into public Actions artifacts.

The first diagnostic is `tools/audit_doctorate_runtime.py`, intentionally scoped to A1/A2 materialization and owner-pin/binding state. General account support UI/CLI is a later decision after the usability audit shows which operator questions recur.
