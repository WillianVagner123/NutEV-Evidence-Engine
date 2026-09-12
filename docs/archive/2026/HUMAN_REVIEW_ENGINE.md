# HumanReviewEngine — PR-8

## Objective

PR-8 introduces a reusable, tenant-scoped human review layer without replacing or migrating the existing scientific validation database.

The reusable layer is:

```text
src/nutev/review/
```

It provides the generic primitives required by the multi-tenant platform contract:

```text
ReviewRound
Reviewer
Assignment
Decision
Submit
Lock
Adjudication
Audit event
```

The engine deliberately does **not** know Article 1, Article 2, D-132, scoping review logic, integrative review logic, NutEV ranking, or manuscript-specific rules.

Application-specific projects configure and use this engine in later PRs.

---

## Architecture

```text
Workspace
└── Project
    └── ReviewRound
        ├── Reviewer (authenticated user)
        │   └── Assignments
        ├── Reviewer (guest token)
        │   └── Assignments
        ├── Decisions
        └── Adjudication
```

The storage layer is private and tenant-scoped:

```text
SQLiteHumanReviewStore
```

The orchestration and authorization layer is:

```text
HumanReviewEngine
```

The global bibliographic Registry is not copied into this database by the engine. A caller supplies only the assignment payload intentionally needed for the review round.

---

## Permission model

PR-8 adds two centralized permissions:

```text
human_review.read
human_review.manage
```

Minimum role behavior:

```text
WORKSPACE_OWNER    read=full      manage=full
WORKSPACE_ADMIN    read=full      manage=full
RESEARCHER         read=full      manage=full
REVIEWER           read=assigned  manage=none
VIEWER             read=full      manage=none
GUEST_REVIEWER     read=assigned  manage=none
```

Saving/submitting an authenticated review still requires an actual assignment and the existing assigned `SCREEN` permission. Adjudication continues to use the centralized `ADJUDICATE` permission.

`PLATFORM_ADMIN` remains infrastructure-only and is not a bypass for private review data.

---

## Guest reviewer security

Guest access uses a cryptographically strong token generated with `secrets.token_urlsafe(32)`.

Persistence contains only:

```text
token_hash = SHA-256(token)
expires_at
revoked_at
round_id
reviewer_id
```

The raw token is returned only at issuance and is not recoverable from the review database.

Rules:

```text
invalid token  -> deny
manipulated    -> deny
expired        -> deny
revoked        -> deny
wrong round    -> deny
wrong reviewer -> deny
```

A future web client must continue the contract from the platform specification:

```text
#token=<secret>
```

The token must be converted to an Authorization header by the browser and must not be placed in query parameters, logs, analytics or persistent browser storage.

PR-8 itself does not add a public guest URL yet; that is part of the first application integration in PR-9.

---

## Backend field blinding

Each assignment has:

```text
payload
allowed_fields
```

`review_payload()` reconstructs the reviewer response only from fields explicitly present in `allowed_fields`.

This is a backend filter. It is not a CSS/UI hiding mechanism.

Therefore a future D-132 assignment can provide:

```text
title
abstract
DOI
PMID
full text descriptor when authorized
eligibility criteria
```

while excluding:

```text
R1 decision
NutEV rank
NutEV score
machine relevance
other reviewer decision
```

The generic engine contains none of those manuscript-specific fields; the application adapter decides the allowlist.

---

## Decision contract

A round can define a small reusable policy:

```text
decision_options
reason_required
minimum_reviewers_per_item
```

The engine does not hardcode a scientific scale.

For example, the legacy validation currently uses `0/1/2`; an application may configure those values without making them part of the engine.

Once a reviewer submits:

```text
submitted_at = timestamp
locked_at = timestamp
```

Subsequent decision writes fail.

The lock is a scientific integrity boundary.

---

## Adjudication

Adjudication cannot open until every reviewer in the round has submitted and locked.

For each `item_key`:

```text
same decisions -> agreement
mixed decisions -> conflict
```

The configured minimum number of independent reviewers is enforced before adjudication.

Only conflicts may receive an adjudication record.

A round can be finalized only when all conflicts have a human adjudication.

No reviewer decision is silently overwritten by adjudication; original decisions and final adjudication are stored separately.

---

## Audit trail

The engine records events such as:

```text
round_created
reviewer_added
guest_reviewer_issued
guest_reviewer_revoked
assignment_created
decision_saved
reviewer_submitted_locked
conflict_adjudicated
adjudication_complete
```

Raw guest tokens are never written to audit details.

---

## Legacy validation compatibility

The existing implementation remains untouched in PR-8:

```text
apps/nutev-web/validation_server.py
apps/nutev-web/validation_adjudication.py
project_output_reference/16_validation_server/validation.sqlite3
```

That legacy database currently stores raw reviewer tokens. PR-8 does **not** copy those tokens into the new system and does not mutate that database.

This is intentional.

The migration path is:

```text
current validation stays operational
        ↓
HumanReviewEngine proves reusable contracts
        ↓
PR-9 instantiates an Article 1 review round
        ↓
legacy validation may later be migrated by an explicit, reviewed migration
```

There is no destructive schema merge in PR-8.

---

## Death tests

PR-8 adds tests for:

```text
raw guest token absent from SQLite
manipulated token denied
revoked token denied
expired token denied
backend allowed_fields filtering
other reviewer assignment hidden
cross-reviewer write denied
cross-tenant round ID -> not found
cross-project round ID -> not found
removed membership -> authorization denied
submit -> immutable lock
two independent reviewers required
adjudication blocked before all submits
conflict detection
human adjudication
finalization only after conflict resolution
reviewer cannot manage round
legacy validation module remains present
engine contains no Article 1 / Article 2 / D-132 hardcode
```

Existing validation tests remain part of the full repository CI and are the backward-compatibility gate.

---

## Scientific impact

PR-8 does not:

```text
execute a search
change providers
change ranking
change article_id
change Registry data
migrate A1
migrate A2
change legacy reviewer decisions
change screening decisions
change extraction
recreate PRISMA
```

It creates only new empty review infrastructure and test fixtures.

---

## Migration impact

No historical scientific data is migrated in PR-8.

PR-7's production-volume dry-run remains a separate operational gate. At the time PR-8 was started, production SSH access was still blocked because the GitHub Environment secret `HETZNER_SSH_KEY` could not be parsed as an unencrypted private key. That deployment/access blocker must be fixed before the real `project_output*` dry-run can run.

This does not authorize skipping the dry-run before any historical ownership activation.

---

## Rollback

Rollback is code-only:

```text
revert PR-8
```

No legacy database conversion or scientific-state mutation is performed, so there is no scientific rollback procedure in this PR.

---

## Next step

After PR-8 is fully green and merged:

```text
PR-9 — Article 1 / D-132
```

PR-9 may instantiate the generic engine for the Article 1 professor/verifier portal with:

```text
private guest link
backend blinding
D-132 sampling configuration
assigned items only
no A2 access
no workspace-wide access
```

The application must remain a client of HumanReviewEngine; no A1-specific behavior should be moved into the reusable engine.
