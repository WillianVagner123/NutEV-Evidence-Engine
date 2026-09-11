# Publication readiness: 1.1.0 candidate

Status: **UNPUBLISHED / production acceptance pending**. Prior stable GitHub release
v1.0.0 was rechecked through the Releases API. Its tag and archived identity are
unchanged. This document does not claim a new Zenodo deposit or DOI.

## Distribution scope

The `nutev-nutmev` wheel and sdist distribute the reusable Python modules and CLI.
The explicit PDM package allowlist excludes runtime data, accounts, databases,
private A1/A2 search configurations and server backups. The website and its
source-checkout tools are deployed from the audited Git commit, not installed by
the wheel. This distinction is deliberate and must remain in release notes.

The candidate version is 1.1.0: CLI/library distribution identity is retained,
while authenticated workspaces/projects and release controls are added. Pilot
mode intentionally blocks unscoped legacy scientific surfaces. Operators
requiring those surfaces must review migration rather than bypass authorization.
The old v1.0.0 DOI is not assigned to this candidate; current CFF/Zenodo metadata
omit a new release date/DOI until there is a real publication record.

## Reproducible checks

- Full tests: `PYTHONPATH=src python -m pytest -q nutev_tests`.
- Build: `python -m build`; validate wheel/sdist with `python -m twine check dist/*`.
- Public-file policy: `python tools/audit_public_package.py --dist dist --version 1.1.0 --output package_audit/distributions.json`.
- Isolated installation: install the wheel in a clean virtual environment, copy
  `tools/installed_package_smoke.py` outside the checkout and execute it with that
  interpreter's `-I` mode. Source code cannot shadow the installed package.
- Container: `bash tools/run_container_release_gate.sh` uses only disposable
  local Docker resources. It injects five random synthetic private canaries,
  verifies their exclusion from the Docker build context, builds the actual
  image, checks pilot HTTP/runtime identity and rehearses restoration with
  numeric uid/gid 10001. It never accepts a production host or volume argument.

Archive policy rejects malformed/duplicate paths, links, unexpected modules or
metadata, oversized members, private runtime types and selected embedded secret
markers. It is not a general proof of copyright compliance or absence of all
personal information. Gitleaks/CodeQL and human review remain separate gates.

## Hosted installation contract

Production requires `NUTEV_AUTH_MODE=pilot`. Accounts/workspaces are provisioned
administratively through the existing operator tooling; there is no public
self-service signup promise. The sample server environment now matches pilot
and leaves A2 dark-launched. A1 owner pins must come from reviewed runtime
ownership evidence. Do not copy IDs from sample data.

## Recovery contract

Snapshot schema 2 inventories regular files AND empty directories, numeric uid/gid
and mode. Restoration must match that metadata as well as byte hashes, followed
by SQLite/WAL integrity checks in the restored copy. Schema-1 development
snapshots lack metadata proof and are rejected instead of silently promoted.
Creating a fresh quiesced snapshot is the migration path; existing production
snapshots are not rewritten automatically. Restoring foreign ownership requires
appropriate OS privileges and must fail when unavailable. ACLs/xattrs are not
currently certified; an estate depending on them needs additional reviewed
recovery coverage before promotion. Quiescence of every actual writer and real
storage capacity remain server-side acceptance checks.

## Final gates still requiring external evidence

No public release/tag/deposit is created until the actual candidate, main SHA,
build artifacts and intended hosted runtime have passed their respective gates.
SSH setup, trusted host pin, real data/owner inventory, actual backup compatibility,
controlled deployment and public smoke belong to the final runtime stage.
A1 methodological approvals and A2 LegacyBindingEvidence remain independent.
Code tests may pass while those scientific projects remain correctly blocked.

## Evidence custody

Test outcomes, commit SHA, synthetic merge SHA, artifacts and hashes belong in the
release manifest. A later commit invalidates a prior candidate's blanket PASS.
Candidate distributions uploaded as CI artifacts are not GitHub Releases, PyPI
publications or Zenodo deposits. Retain the final audit outside expiring CI
storage before publishing, without retaining private test credentials.

## Generic CLI boundary

The new `science-topics` command requires an explicit `--topic-profile`. It no
longer silently chooses the private A1 profile. The archived v1.0.0 CLI exposed
only version/help/providers, so this correction does not remove a released
v1.0.0 command contract. Existing source-checkout scripts using the unreleased
implicit A1 default must pass their reviewed profile explicitly. No profile
content or search vocabulary was changed.
