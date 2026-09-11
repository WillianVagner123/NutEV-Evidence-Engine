# Closeout baseline — 2026-09-10

Main observed: `0c354e23150f74692cd623007c5acc27a93fe28b`, PR #1245, committed 2026-09-08T20:34:27Z. This is the code baseline, not a production identity claim.

## Remote evidence

- CI: https://github.com/WillianVagner123/NutEV-Evidence-Engine/actions/runs/34275597931
- Chromium: https://github.com/WillianVagner123/NutEV-Evidence-Engine/actions/runs/34275598054
- CodeQL: https://github.com/WillianVagner123/NutEV-Evidence-Engine/actions/runs/34275598024
- Failed deployment: https://github.com/WillianVagner123/NutEV-Evidence-Engine/actions/runs/34275710592
- New hermetic audit: https://github.com/WillianVagner123/NutEV-Evidence-Engine/actions/runs/34537074947

Baseline CI jobs 102227706267/102227706270 (Python 3.12/3.13), 102227706318 (Windows), 102227706352 (blocking Ruff), 102227705897 (provenance typecheck), and 102227706289 (guardrail contracts) succeeded. Typing covers configured provenance files, not the whole repository. Advisory style checks are not a style-clean assertion. CodeQL Python job 102227706386 and Chromium job 102227706320 succeeded.

Dependency review originally ran only on pull requests; artifact validation ran only on pull requests/manual dispatch. Neither absence is PASS on the merge SHA. The deploy workflow originally waited only for ci; manual dispatch likewise lacked the complete prerequisite barrier. The candidate fixes these execution gaps. Remaining security/check conclusions must be read on the exact final candidate rather than inherited from baseline.

## Source custody and local execution

The connector downloaded artifact 10175813040 from audit run 34537074947. ZIP SHA-256: `04a3040f91766e3ba62e7fd3c309a2996e3dd763d87fcff5e279411a6ebbc16b`. Inner source archive SHA-256: `0851aeeddfe323a6f65c3588da18c4a47b7a9ce46f04ed90fb9db93497349894`. Source commit: `bb2e93e43fab239e77039ae991934cfba13df513`. The archive contains tracked source, not production volumes.

For candidate local tests, overlays were the exact release verifier, its two test modules, and deploy/dependency/artifact workflow updates proposed in code candidate `c45e302a3a8cdbac3b8721fe6020320aebd9e98f`.

Executed on Python 3.13.5:

| Execution | Result |
|---|---|
| `PYTHONPATH=src python -m pytest -q nutev_tests` | 999 passed in 48.36s |
| Targeted release verifier + workflow contracts | 84 passed |
| Existing hermetic tenant CLI | 17 checks PASS locally and in the cited remote audit |
| Parse changed workflow YAML | 4 files valid |
| `bash -n` on changed workflow shell bodies | 14 checks PASS |

Initial local full-suite invocation incorrectly added `NUTEV_DISABLE_NETWORK=1` globally: 998 passed and one mocked-provider test failed because the flag bypassed its fake provider. Repeating the canonical CI command without that injected flag produced 999 passes; no application logic, assertion or provider semantics were weakened. An earlier tool-bounded invocation was interrupted before completion and is not counted as PASS.

## Coverage still pending

Full branch aging/release history/issue census, every TODO/FIXME and skipped-test audit, patch-level review of all old PRs, authenticated pilot UI matrix, live version/auth, production data counts/hashes, full-text grants in production, migration application and actual restore rehearsal. This baseline does not claim those phases complete.

## Read sources

AGENTS.md; AI_CONTEXT.md; ARTICLE1_SEARCH_MASTER.md and its two JSON control files; ARTICLE1_AGENT_CONTEXT; A2 workflow; migration inventory; full tenant death-test and final release contract; architecture; CI/security/deploy workflows. D-132 verification document is absent from baseline main and was read from PR #1230 head `a460404bcf6b447df6a8d9bc68584dc6af9034cf` as a proposal.

Historical inventory PR-0 is not a current assertion that later identity/A2 modules do not exist. Its runtime-ownership warning remains applicable. AI_CONTEXT and ARTICLE1_AGENT_CONTEXT still contain legacy URL guidance; pilot access must follow FINAL_MULTITENANT_RELEASE_GATE.md, not an assumption of public access.

## Follow-up closeout: SSH deliberately last

2026-09-10 America/Sao_Paulo: new HTTP/browser/recovery evidence supersedes the earlier missing-coverage entries, not the historical counts above. Full final local suite: 1,044 PASS (Python 3.13.5), including the last A1 source-owner correction. Head 5b7970373ef0dc49581ad742838e982c23605767 completed all seven PR workflows; its authenticated Chromium artifact contains 12 PASS scenarios. The next commit adds the final A1 fix and these reports, and requires its own CI verification.

Actual defects fixed include unscoped pilot surfaces, stale tab/response context, concurrent export rendering and trusting an editable A1 application label as source ownership. Recovery now preserves prior configuration and requires a quiesced verified snapshot/isolated restore proof; host identity is explicitly pinned. SSH/server operations were not attempted. The first CI attempt's missing YAML dependency and browser failures are retained in the evidence history.
