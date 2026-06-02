import json
from pathlib import Path


SOURCES_PATH = Path("config/global_watch_sources.json")


def _sources_by_institution() -> dict[str, dict]:
    sources = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    return {source["institution"]: source for source in sources}


def test_global_watch_includes_obesity_guideline_authorities():
    sources = _sources_by_institution()

    assert "Obesity Canada" in sources
    assert "European Association for the Study of Obesity" in sources

    for institution in (
        "Obesity Canada",
        "European Association for the Study of Obesity",
    ):
        source = sources[institution]
        assert "guidelines_consensus" in source["categories"]
        assert "cardiometabolic_risk" in source["categories"]
        assert "busca2a" in source["workstream_affinity"]
        assert "busca2b" in source["workstream_affinity"]
        assert any("guideline" in pattern for pattern in source["allowed_patterns"])
        assert "obesity" in source["allowed_patterns"]
