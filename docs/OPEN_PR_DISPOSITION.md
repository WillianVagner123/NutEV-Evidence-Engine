# Open PR disposition — preliminary closeout census

Audit date: 2026-09-10. Baseline main: `0c354e23150f74692cd623007c5acc27a93fe28b`.

46 pre-existing open PRs were enumerated using connected search, including three Dependabot PRs. REST listing with per_page=1 returned #70 on page 46 and an empty page 47. This predates the newly opened closeout PR #1246 (47 total if no concurrent changes).

Classification is preliminary and is NOT patch approval, proof of duplication, or permission to close. During the initial census no old PR was merged, closed or force-pushed; see the dated follow-up below for the single subsequently verified closure. Every old head still needs a comparison against current main before a terminal disposition. No item is called SUPERSEDED/CLOSE_SAFE solely because its title looks old.

| PR | Disposition | Reason / required next evidence |
|---|---|---|
| #1230 | BLOCKED | D-132 proposal; academic approval and named human verifier not established by repository draft |
| #1128 | BLOCKED | Optional web providers overlap later registry work; prove exact delta before calling superseded |
| #112 | BLOCKED | Search regression coverage; reconcile old test assumptions with current semantics |
| #73 | BLOCKED | Claimed provider/query-budget behavior requires current-code comparison; do not merge on title |
| #126 | FUTURE_BACKLOG | Search/vocabulary expansion outside closeout; patch review pending |
| #124 | FUTURE_BACKLOG | Search/vocabulary expansion outside closeout; patch review pending |
| #123 | FUTURE_BACKLOG | Instrument watch vocabulary expansion; patch review pending |
| #122 | FUTURE_BACKLOG | Scientific search expansion outside freeze; patch review pending |
| #121 | FUTURE_BACKLOG | Scientific search expansion outside freeze; patch review pending |
| #120 | FUTURE_BACKLOG | Food-access terms; no demonstrated release blocker |
| #119 | FUTURE_BACKLOG | Scientific search expansion outside freeze; patch review pending |
| #118 | FUTURE_BACKLOG | Scientific search expansion outside freeze; patch review pending |
| #117 | FUTURE_BACKLOG | Clinical guidance terms; no demonstrated release blocker |
| #116 | FUTURE_BACKLOG | Scientific search expansion outside freeze; patch review pending |
| #115 | FUTURE_BACKLOG | Sodium watch/scoring expansion |
| #114 | FUTURE_BACKLOG | Scientific search expansion outside freeze; patch review pending |
| #113 | FUTURE_BACKLOG | Diet-quality watch vocabulary |
| #111 | FUTURE_BACKLOG | Scientific search expansion outside freeze; patch review pending |
| #110 | FUTURE_BACKLOG | Lifestyle-medicine query phrases |
| #109 | FUTURE_BACKLOG | Hepatic clinical query block |
| #108 | FUTURE_BACKLOG | Chrononutrition retrieval expansion |
| #107 | FUTURE_BACKLOG | A3 psychometric cues |
| #106 | FUTURE_BACKLOG | Scientific search expansion outside freeze; patch review pending |
| #105 | FUTURE_BACKLOG | Adiposity/clinical-obesity terms |
| #104 | FUTURE_BACKLOG | Lifestyle-medicine phrase variants |
| #103 | FUTURE_BACKLOG | Fatty-liver expansion/prioritization |
| #101 | FUTURE_BACKLOG | Practical food-skills retrieval |
| #100 | FUTURE_BACKLOG | Liver-guidance retrieval |
| #99 | FUTURE_BACKLOG | Food-security/environment signals |
| #98 | FUTURE_BACKLOG | Digital-delivery query expansion |
| #97 | FUTURE_BACKLOG | Multilingual commensality scoring |
| #96 | FUTURE_BACKLOG | Taxonomy expansion outside freeze |
| #81 | FUTURE_BACKLOG | Hepatic-fat scoring |
| #80 | FUTURE_BACKLOG | Scientific search expansion outside freeze; patch review pending |
| #79 | FUTURE_BACKLOG | Behavior-change watch vocabulary |
| #78 | FUTURE_BACKLOG | Scientific search expansion outside freeze; patch review pending |
| #77 | FUTURE_BACKLOG | Hepatic-steatosis watch vocabulary |
| #76 | FUTURE_BACKLOG | Food-is-medicine program scoring |
| #75 | FUTURE_BACKLOG | Psychometric watch expansion |
| #74 | FUTURE_BACKLOG | Food-is-medicine query coverage |
| #72 | FUTURE_BACKLOG | Lipid-risk watch signals |
| #71 | FUTURE_BACKLOG | Policy/practice guidance labels |
| #70 | FUTURE_BACKLOG | Implementation/adherence prioritization |
| #1163 | FUTURE_BACKLOG | CodeQL action update; assess security need and compatibility separately |
| #1164 | FUTURE_BACKLOG | CodeQL action update; assess security need and compatibility separately |
| #1165 | FUTURE_BACKLOG | CodeQL action update; assess security need and compatibility separately |

Totals: BLOCKED 4; FUTURE_BACKLOG 42. Scope classification can change if an actual blocker/security advisory is established. PR source URLs use `https://github.com/WillianVagner123/NutEV-Evidence-Engine/pull/<number>`.

New PR #1246 is the active closeout candidate, not one of the 46 legacy items. Its code can only be integrated after review and required checks. Keeping scientific proposals blocked is intentional, not a reason to fabricate approval or delete work.

## Patch-reviewed follow-up (2026-09-10, America/Sao_Paulo)

- #1128: **SUPERSEDED, closed unmerged**. Its patch was read and compared with current search_adapter.py and test_web_optional_provider_contract.py. Optional web providers, caps and partial/skipped propagation are already implemented; all 5 current provider-contract tests passed. Evidence comment 5627117413 and closure are on #1128. Branch/history preserved.
- #112: patch read. It imports historical nutev.querypacks modules absent from the current supported source; not a safe direct merge. Reclassify as **FUTURE_BACKLOG**, requiring an explicit port/review if those historical assumptions are still needed. No scientific vocabulary was reintroduced.
- #73: patch read. It changes the historical src/nutev/pipelines/master_pipeline.py rather than the current supported engine. Reclassify as **FUTURE_BACKLOG**; this is not proof of a current release defect or authorization to reintroduce the old pipeline.
- #1230 remains **BLOCKED_SCIENTIFIC** as a proposed academic verification contract.

Disposition of the 46 pre-existing items after this review: 1 closed SUPERSEDED (#1128), 1 BLOCKED (#1230), 44 FUTURE_BACKLOG (the prior 42 plus #112/#73). Only the cited patches were inspected individually; this is not a claim that all 44 future diffs were tested or obsolete. Including active #1246 gives 46 open PRs absent concurrent changes.
