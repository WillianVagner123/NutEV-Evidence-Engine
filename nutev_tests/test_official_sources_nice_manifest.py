from __future__ import annotations

import json
from pathlib import Path

from nutev.search.official_sources import manifest_sources


ROOT = Path(__file__).resolve().parents[1]


def _official_manifest() -> dict:
    return json.loads((ROOT / "config" / "official_sources_manifest.json").read_text())


def test_nice_cardiometabolic_guidelines_are_available_for_busca2a() -> None:
    sources = manifest_sources(_official_manifest(), "busca2a")
    names = {str(source["title"]).lower() for source in sources}

    assert "nice overweight and obesity management guideline ng246" in names
    assert "nice type 2 diabetes in adults management guideline ng28" in names
    assert (
        "nice cardiovascular disease risk assessment and lipid modification guideline ng238"
        in names
    )


def test_nice_obesity_guideline_supports_intervention_workstream() -> None:
    sources = manifest_sources(_official_manifest(), "busca2b")
    urls = {source["url"] for source in sources}

    assert "https://www.nice.org.uk/guidance/ng246" in urls
