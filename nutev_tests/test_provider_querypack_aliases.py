from pathlib import Path

from nutev.querypacks.provider_queries import build_provider_querypack
from nutev.settings import load_json


def test_provider_querypack_preserves_a3_alias_and_canonical_key() -> None:
    taxonomy = load_json(Path("config") / "keyword_taxonomy.json")

    provider_querypack = build_provider_querypack(
        taxonomy,
        ["a3"],
        {"a3": ["pubmed", "europepmc", "official_web"]},
    )

    assert "a3" in provider_querypack
    assert "artigo3_framework" in provider_querypack
    assert provider_querypack["a3"] == provider_querypack["artigo3_framework"]
    assert provider_querypack["a3"]["pubmed"]
    assert provider_querypack["a3"]["europepmc"]
