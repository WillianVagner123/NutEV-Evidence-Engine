# Contributing to NutEV/NutMEV

Thank you for your interest in contributing to **NutEV/NutMEV — Evidence Engine for Lifestyle Nutrition**.

NutEV/NutMEV is a scientific and methodological platform for identifying, classifying, auditing, and translating evidence into **candidate recommendations** for the NutEV dietary protocol. The canonical runtime for the doctorate project is `src/nutev/`.

This repository evolved from a historical Local Deep Research base. Some legacy files and compatibility entry points may still exist, but new research, qualification, and protocol-development work should target the NutEV/NutMEV architecture.

## Project principles

1. **Scientific traceability first.** Evidence must be traceable from document to claim to recommendation candidate.
2. **No unsupported recommendations.** A `RecommendationCandidate` is not a final recommendation.
3. **Human review is required.** Final protocol inclusion requires explicit human validation.
4. **LLM is assistive only.** LLM output cannot approve protocol items, replace reviewers, or create support without documentary evidence.
5. **Small PRs are safer.** One intent per PR: UI, audit, rigor, docs, or pipeline.

## Canonical NutEV workflow

The expected evidence-to-protocol chain is:

```text
Document -> EvidenceRecord -> EvidenceClaim -> ClaimEvaluation -> RecommendationCandidate -> HumanReview -> ProtocolReadiness
```

New code should preserve this chain and should not bypass audit or human review safeguards.

## Before you start

- Open or reference an issue for larger changes.
- Keep PRs small and atomic.
- Prefer additive changes over broad rewrites.
- Avoid mixing UI, scientific methods, search strategy, and pipeline changes in the same PR.
- Do not commit generated real outputs, secrets, or large files.

## Development setup

Install the project locally:

```bash
python -m pip install -e ".[dashboard,platform]"
```

Generate demo outputs:

```bash
nutev demo-data --project-root ./project_output_demo
```

Run the local platform API:

```bash
nutev serve --project-root ./project_output_demo --host 127.0.0.1 --port 8000
```

Run the Control Center:

```bash
nutev dashboard --project-root ./project_output_demo --port 8501
```

Run NutEV tests:

```bash
PYTHONPATH=src python -m pytest -q nutev_tests
```

## Pull request expectations

A good PR should include:

- a clear title;
- a short explanation of why the change is needed;
- files changed only for one concern;
- tests or a clear note if tests were not run;
- documentation updates when user-facing behavior changes.

Recommended PR scopes:

- `fix(cli): ...`
- `feat(audit): ...`
- `feat(rigor): ...`
- `feat(ui): ...`
- `docs(nutev): ...`
- `test(nutev): ...`

## Safety rules for contributions

Do not commit:

- API keys, tokens, credentials, or `.env` files;
- real patient or participant data;
- unreviewed generated outputs from real searches;
- large binary files;
- private PDFs or copyrighted full-text files without permission.

Generated folders such as `project_output/` and `project_output_demo/` should remain local unless intentionally added as small, clearly marked demo fixtures.

## Scientific rules

When contributing to evidence, audit, or protocol modules:

- keep exact quotes when available;
- preserve `document_id`, `claim_id`, and `recommendation_id` links;
- mark computational inference as requiring human review;
- do not convert gaps into final recommendations;
- do not hide conflicting evidence;
- do not let LLM output set `approved`, `approved_for_protocol`, or `locked_for_protocol`.

## Repository structure

Canonical NutEV areas:

```text
src/nutev/audit/
src/nutev/analysis/
src/nutev/api/
src/nutev/demo/
src/nutev/export/
src/nutev/global_watch/
src/nutev/pipelines/
src/nutev/protocol/
src/nutev/review/
src/nutev/ui/
config/
docs/
nutev_tests/
```

The inherited `src/local_deep_research/` engine has been removed (see `NOTICE.md`
and `docs/LEGACY_MIGRATION_PLAN.md`). All work targets `src/nutev/`.

## Documentation

Useful project documents:

- `README.md`
- `SECURITY.md`
- `docs/REPOSITORY_STRUCTURE.md`
- `docs/VALIDATION_REPORT.md`
- `docs/NUTEV_AUDIT_ENGINE.md`
- `docs/NUTEV_CONTROL_CENTER.md`
- `docs/NUTEV_PLATFORM_API.md`
- `docs/NUTEV_PREMIUM_UI_GUIDE.md`
- `docs/NUTEV_EVIDENCE_TO_PROTOCOL_FLOW.md`

## Code of conduct

- Be respectful and constructive.
- Make methodological assumptions explicit.
- Prefer transparent limitations over overclaiming.
- Protect the scientific integrity of the NutEV protocol.

Thank you for helping build NutEV/NutMEV.
