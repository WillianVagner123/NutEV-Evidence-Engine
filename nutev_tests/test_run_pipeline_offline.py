"""run_pipeline runs the audit stage as a first-class step, offline.

The audit/claims stage used to exist only because a runtime_compat monkey-patch
was applied before run_pipeline (and T1b made run_pipeline self-apply it). After
the runtime_compat migration the audit finalization is a plain call inside
run_pipeline (nutev.export.curation_finalize), so it always runs — no bootstrap,
no hidden dependency. This exercises it end-to-end with the network disabled.
"""
from __future__ import annotations

import logging

from nutev.settings import NutevSettings


def test_run_pipeline_offline_produces_audit_stage(tmp_path, monkeypatch):
    monkeypatch.setenv("NUTEV_DISABLE_NETWORK", "1")  # no network in the test

    from nutev.pipelines.master_pipeline import run_pipeline

    settings = NutevSettings(project_root=tmp_path)
    for d in settings.output_dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    summary = run_pipeline(settings, ["busca1"], logging.getLogger("test.run_pipeline"))

    # The first-class audit stage ran: its metric is in the summary...
    assert "evidence_claims_total" in summary
    # ...and the audit CSVs land where the dashboard/API read them (02_metadata).
    assert (tmp_path / "02_metadata" / "NUTEV_EVIDENCE_CLAIMS.csv").exists()
    assert (tmp_path / "02_metadata" / "NUTEV_RECOMMENDATION_CANDIDATES.csv").exists()
