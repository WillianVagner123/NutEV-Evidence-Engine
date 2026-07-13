<!-- Thank you for contributing to NutEV/NutMEV. Please fill in the sections below. -->

## Summary

<!-- What does this PR change and why? -->

## Type of change

- [ ] Bug fix
- [ ] Feature / enhancement
- [ ] Documentation
- [ ] Methodology / rules / scoring / ontology change
- [ ] New source / query pack
- [ ] Build / CI / dependencies
- [ ] Legacy isolation (see docs/LEGACY_MIGRATION_PLAN.md)

## Scientific integrity checklist

- [ ] No output is presented as a final clinical recommendation (candidates only).
- [ ] New claims are traceable to a source document + verifiable location.
- [ ] Conflicts are surfaced, not hidden.
- [ ] No LLM is used to define final approval.
- [ ] Methodology/rule/scoring changes are versioned (methodology changelog).

## Safety checklist

- [ ] No secrets, tokens, `.env`, private keys, or signed URLs.
- [ ] No personal, patient, or participant data.
- [ ] No protected full texts / third-party PDFs (share DOI/URL/metadata instead).
- [ ] No real run outputs or local databases committed.

## Testing

- [ ] `PYTHONPATH=src python -m pytest -q nutev_tests` passes (or explain).
- [ ] `nutev` still works (`nutev demo-data --project-root ./project_output_demo`).

## Docs

- [ ] Docs updated where relevant.

## Notes for reviewers

<!-- Anything the reviewer should focus on. -->
