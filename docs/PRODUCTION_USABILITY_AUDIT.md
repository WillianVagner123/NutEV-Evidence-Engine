# Production usability audit — NutEV 1.1.0

Baseline: stable `v1.1.0`, production accepted, GitHub/Zenodo publication complete. This audit evaluates practical task completion separately from security correctness and scientific validity.

## Current findings

### UX-01 — first login with no workspace — CLOSED

A provisioned identity with zero workspace memberships now receives explicit guidance instead of an ambiguous empty selector:

- `Acesso ainda não provisionado`;
- login/session are acknowledged as working;
- the UI explains that an administrator must grant/create the workspace.

The authenticated Chromium fixture requires the same state on the home/context surface and the project page.

### UX-02 — first project with zero ResearchApplications — CLOSED BY BROWSER GATE

The synthetic pilot fixture includes an `onboarding` user with a real workspace/project and **zero applications**. The authenticated Chromium path must:

1. log in;
2. select workspace/project;
3. open `/project.html`;
4. see the three supported application templates;
5. configure `GENERIC_EVIDENCE_PROJECT` through the real UI;
6. verify visible next actions for **Buscar evidências**, **Biblioteca** and **Exportações**;
7. reload the project and verify the configured application persists;
8. log out, log in again, reselect the same context and verify the application and next actions still persist.

The persistence regression is a separate Playwright script executed inside the required `Authenticated pilot browser closeout` job, so a failure blocks the product gate.

### UX-03 — Review is not first-class navigation — DEFERRED BY SCOPE, NOT SILENTLY PROMOTED

The current `/review.html` surface is still explicitly tied to **Article 1 calibration/formal-screening readiness**. It is not a generic ResearchApplication-scoped review surface. Promoting it into primary navigation for every project would therefore create a false product contract.

Current decision:

- keep generic primary navigation focused on Project, Search, Library, Exports and History;
- keep specialized review tooling under the advanced/scientific surfaces;
- promote Review only after a generic, tenant/project/application-scoped review route exists and passes the same isolation/browser gates.

This remains a product opportunity, not a justification to expose Article-1-specific state globally.

### UX-04 — hosted product vs local scientific server — CLOSED DOCUMENTATION GAP

The web documentation now names two distinct runtimes:

- **Hosted product runtime** — authenticated, multi-tenant, production-facing; ordinary users work through workspace/project/application context.
- **Local scientific/validation runtime** — `apps/nutev-web/server.py`, intended for localhost/LAN scientific coordination and validation; it must not be treated as the public hosted product.

The local-server warning remains fail-closed: do not expose it directly to the public internet.

### UX-05 — repository/product history mixed with live documentation — CLOSED IN DOCUMENTATION CLEANUP

Historical release gates, smoke reports, sprint closeouts and migration dry-runs are moved under `docs/archive/2026/`. Truly transient, superseded documents are deleted. `docs/README.md` now acts as a maintained index of current documentation rather than an inventory of every historical artifact.

## Product-use evidence still worth collecting

A moderated production-use pass with a real non-admin test account remains valuable for measuring confusion rather than correctness:

`login -> context -> project -> application -> search -> library -> review discovery -> export -> logout`

Use only synthetic content/screenshots. Do not use A1/A2 private content in public UX artifacts.

## Scientific boundary

Usability PASS does not change scientific status. The general scientific verdict remains `B — DEMOTE` until independent benchmark evidence supports a different verdict.