from __future__ import annotations

from nutev.search.official_sources import manifest_sources


def test_manifest_sources_dedupes_normalized_urls_across_aliases() -> None:
    manifest = {
        "workstreams": {
            "artigo3_framework": [
                {
                    "name": "Brazilian Dietary Guidelines",
                    "url": "https://www.example.org/guidelines/",
                }
            ],
            "a3": [
                {
                    "name": "Brazilian Dietary Guidelines duplicate",
                    "url": "https://example.org/guidelines",
                },
                {
                    "name": "Food literacy framework",
                    "url": "https://example.org/food-literacy",
                },
            ],
        }
    }

    rows = manifest_sources(manifest, "a3")

    assert [row["url"] for row in rows] == [
        "https://www.example.org/guidelines/",
        "https://example.org/food-literacy",
    ]
