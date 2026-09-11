# Production usability audit — Sprint 15

Baseline: NutEV 1.1.0 deployed. This audit evaluates practical task completion separately from security correctness.

## Initial findings

### UX-01 — first login with no workspace did not explain the operational next step — P1

The authenticated context selector could render an empty workspace list while the user had no way to distinguish a broken system from an account awaiting administrative provisioning. Public signup is intentionally unsupported, so the correct fix is guidance, not a signup feature.

**Patch:** show `Acesso ainda não provisionado`, confirm that login works and tell the user that an administrator must create/grant the workspace. Project page uses the same distinction.

**Regression:** Chromium fixture adds a real authenticated user with zero workspace memberships and requires this guidance.

### UX-02 — project with no application needs a complete first-project path — P1 test gap

The project page already exposes three reusable templates and a `Configurar aplicação` action, but the prior browser acceptance skipped this state because all fixture projects were preconfigured.

**Action:** add an onboarding user with a workspace/project but no application; configure `GENERIC_EVIDENCE_PROJECT` through the real UI and require visible next actions for Search, Library and Exports.

### UX-03 — review is not a first-class navigation item — P2 candidate

`Revisão humana` is reachable from the project module grid but primary navigation places it under `Laboratório avançado`. This may be appropriate for generic projects and wrong for active review templates. Do not redesign yet: measure task confusion in the next moderated/usability pass before promoting it.

### UX-04 — provisioning is administrative by design — NOT A BUG

There is no self-service account/workspace creation. Documentation states that identities are explicitly provisioned and passwords are never passed on the CLI. The UI must therefore explain waiting/provisioning states clearly rather than advertising a signup flow that does not exist.

## Next production-use evidence

After this patch passes fixture Chromium, run the same mental model with a real non-admin test account in production: login; locate project; identify current context; open Search; open Library; identify Review; export; logout. Capture only synthetic content/screenshots. Do not use A1/A2 private content for public UX artifacts.
