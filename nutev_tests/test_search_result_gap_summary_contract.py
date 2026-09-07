from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def test_result_summary_counts_every_provider_gap_class_without_double_counting() -> None:
    js = (WEB / "search-ux-resilience.js").read_text(encoding="utf-8")

    for field in (
        "failed_providers",
        "unavailable_providers",
        "partial_providers",
        "skipped_providers",
        "non_exhaustive_providers",
    ):
        assert field in js
    assert "const gaps=new Set()" in js
    assert "function summaryGapCount(data)" in js
    assert "providerGapIds(data).size" in js
    assert "data?.audit_gaps" in js
    assert "kpiValues[3].textContent=String(summaryGapCount(data))" in js


def test_result_summary_keeps_gap_semantics_separate_from_evidence_quality() -> None:
    js = (WEB / "search-ux-resilience.js").read_text(encoding="utf-8")

    assert "Cobertura descreve recuperação das fontes, não qualidade, certeza ou elegibilidade da evidência." in js
    assert "Isso não prova ausência de evidência." in js
