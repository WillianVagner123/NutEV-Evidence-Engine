# CKM search expansion rationale

Date: 2026-06-18

This additive configuration layer expands NutMEV cardiometabolic search coverage for the cardiovascular-kidney-metabolic (CKM) framing while preserving the raw taxonomy and scoring files.

## Scope

- Workstreams: `busca2a` and `busca2b`
- Layer: supplemental config loaded by `nutev.settings.load_json`
- Raw outputs: unchanged

## Rationale

The existing scoring configuration already recognized `ckm syndrome` and long-form cardiovascular-kidney-metabolic terms, but the structured query taxonomy did not consistently inject CKM variants into cardiometabolic workstream query generation. The supplement adds CKM terms as condition and web-hint terms, so provider query rendering can recover guidelines, scientific statements, trials, and lifestyle or dietary intervention records using the newer CKM terminology.

## Noise control

CKM terms are limited to cardiometabolic workstreams and remain anchored by the existing provider query structure, which combines condition, nutrition/diet, document-type, outcome, and implementation blocks. The scoring supplement adds modest prioritization for CKM health/risk variants without changing hard exclusion rules or download thresholds.
