import json

from nutev.settings import load_json


def test_keyword_taxonomy_overlay_merges_lists_without_duplicates(tmp_path):
    taxonomy_path = tmp_path / "keyword_taxonomy.json"
    overlay_path = tmp_path / "keyword_taxonomy_overlay.json"
    taxonomy_path.write_text(
        json.dumps(
            {
                "global": {
                    "implementation_behavior": {
                        "behavioral": ["behavior change", "adherence"]
                    }
                },
                "workstreams": {
                    "busca2b": {"web_query_hints": ["randomized trial"]}
                },
            }
        ),
        encoding="utf-8",
    )
    overlay_path.write_text(
        json.dumps(
            {
                "global": {
                    "implementation_behavior": {
                        "behavioral": [
                            "adherence",
                            "diabetes prevention program",
                            "lifestyle change program",
                        ]
                    }
                },
                "workstreams": {
                    "busca2b": {
                        "web_query_hints": ["diabetes prevention implementation"]
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    merged = load_json(taxonomy_path)

    behavioral_terms = merged["global"]["implementation_behavior"]["behavioral"]
    hints = merged["workstreams"]["busca2b"]["web_query_hints"]
    assert behavioral_terms == [
        "behavior change",
        "adherence",
        "diabetes prevention program",
        "lifestyle change program",
    ]
    assert hints == ["randomized trial", "diabetes prevention implementation"]


def test_non_keyword_taxonomy_json_does_not_auto_merge_overlay(tmp_path):
    config_path = tmp_path / "scoring_rules.json"
    overlay_path = tmp_path / "scoring_rules_overlay.json"
    config_path.write_text(json.dumps({"keyword_points": {"adherence": 2}}), encoding="utf-8")
    overlay_path.write_text(json.dumps({"keyword_points": {"extra": 2}}), encoding="utf-8")

    assert load_json(config_path) == {"keyword_points": {"adherence": 2}}
