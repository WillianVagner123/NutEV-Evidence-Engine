from __future__ import annotations

from nutev.querypacks import semantic_blocks
from nutev.querypacks.cardiovascular_health_metrics_extensions import (
    apply_cardiovascular_health_metrics_extensions,
)


def test_cardiovascular_health_metrics_extension_adds_terms_and_priorities() -> None:
    apply_cardiovascular_health_metrics_extensions()

    block = semantic_blocks.SEMANTIC_RESEARCH_BLOCKS["cardiovascular_health_metrics"]
    assert "life's essential 8" in block["terms"]
    assert "cardiovascular health metrics systematic review" in block["document_terms"]

    for workstream in ("busca1", "busca2a", "busca2b"):
        priorities = semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES[workstream]
        assert priorities[0][0] == "cardiovascular_health_metrics"

    assert semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES["busca1"][0][1] == 3
    assert semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES["busca2a"][0][1] == 5
    assert semantic_blocks.WORKSTREAM_SEMANTIC_PRIORITIES["busca2b"][0][1] == 5
