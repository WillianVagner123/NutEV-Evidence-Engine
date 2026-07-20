"""run_pipeline must self-apply the runtime-compat hooks (T1b).

Before this, the audit/claims stage existed only because cli.main() called
runtime_compat.apply() before run_pipeline. Reaching run_pipeline any other way
(embedded/programmatic use) skipped apply() and silently produced zero claims.
run_pipeline now applies the (idempotent) hooks itself.
"""
from __future__ import annotations

import logging

from nutev.settings import NutevSettings


def test_run_pipeline_invokes_apply_and_runs_audit_stage(tmp_path, monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")  # no network in the test

    import nutev.runtime_compat as rc

    # Simulate "not reached via cli.main": force apply() to be needed again.
    monkeypatch.setattr(rc, "_APPLIED", False)
    calls: list[int] = []
    original_apply = rc.apply

    def spy():
        calls.append(1)
        return original_apply()

    monkeypatch.setattr(rc, "apply", spy)

    from nutev.pipelines.master_pipeline import run_pipeline

    settings = NutevSettings(project_root=tmp_path)
    for d in settings.output_dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    summary = run_pipeline(settings, ["busca1"], logging.getLogger("test.run_pipeline"))

    # run_pipeline applied the hooks itself (not relying on the CLI having done it)...
    assert calls, "run_pipeline did not self-apply runtime_compat"
    # ...and the audit stage ran, so its metric is present in the summary.
    assert "evidence_claims_total" in summary
    # The audit CSVs land where the readers read (02_metadata), even offline.
    assert (tmp_path / "02_metadata" / "NUTEV_EVIDENCE_CLAIMS.csv").exists()
