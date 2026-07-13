# GitHub Public Settings Checklist

Manual configuration to apply in the GitHub UI/settings for a safe, well-presented
public repository. These are **not** code changes — a maintainer applies them.

## Repository presentation

- [ ] **Description:** e.g. "Reproducible evidence engine for lifestyle nutrition
      research — produces RecommendationCandidates (not final clinical advice)."
- [ ] **Topics:** `nutrition`, `lifestyle-medicine`, `evidence-synthesis`,
      `scoping-review`, `open-science`, `reproducible-research`, `python`.
- [ ] **Website:** link to docs or project page (optional).
- [ ] Enable **Discussions**.
- [ ] Enable **Issues** (issue forms already provided).

## Branch protection (`main`)

- [ ] Require a pull request before merging.
- [ ] Require at least **1 approving review**.
- [ ] Dismiss stale approvals on new commits.
- [ ] Require status checks to pass:
      `nutev-tests`, `nutev-lint`, `nutev-smoke`, `security-scan`,
      `dependency-review`, `codeql`.
- [ ] Require branches to be up to date before merging.
- [ ] **Block force pushes** to `main`.
- [ ] Block deletions of `main`.
- [ ] (Recommended) Require signed commits.
- [ ] (Recommended) Include administrators.

## Security & analysis

- [ ] Enable **Secret scanning**.
- [ ] Enable **Push protection** (blocks pushing detected secrets).
- [ ] Enable **Dependabot alerts** and **security updates**
      (`.github/dependabot.yml` present).
- [ ] Enable **Dependency graph**.
- [ ] Enable **CodeQL** default setup or keep the provided `codeql.yml` workflow.
- [ ] Enable **Private vulnerability reporting** (matches `SECURITY.md`).

## Actions

- [ ] Restrict Actions to the repo's own + verified/allowed actions.
- [ ] Set default `GITHUB_TOKEN` permissions to **read-only**; workflows request
      elevated scopes explicitly (already done per-workflow).
- [ ] Require approval to run workflows on PRs from first-time/outside contributors.
- [ ] Confirm `/nutev-tests` comment trigger is author-gated (done in workflow).

## Releases

- [ ] Create the **v0.1.0-alpha** release from `CHANGELOG.md` (mark as pre-release).
- [ ] Attach built artifacts (`dist/*.whl`, `dist/*.tar.gz`) if desired.

## Open-science archival (optional, recommended)

- [ ] Connect **Zenodo** to the repo to mint a **DOI** on release; then update
      `CITATION.cff` (`DOI:` field).
- [ ] Mirror/register on **OSF** if part of the study's registration.

## Forks policy

- [ ] Decide whether forks are allowed (default: yes for open science).
- [ ] Ensure fork PRs cannot access secrets (default GitHub behavior; verified by
      author-gated comment trigger and read-only token defaults).

## Final review

- [ ] `docs/PUBLIC_RELEASE_AUDIT.md` risks addressed or tracked.
- [ ] `.gitleaksignore` re-triaged.
- [ ] No protected content, secrets, personal/clinical data, or real outputs
      present in the repo or in CI artifacts.
