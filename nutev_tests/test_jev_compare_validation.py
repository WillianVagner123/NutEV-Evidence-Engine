from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path
import sys

from nutev.reference_identity import canonical_identity


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "jev_compare_validation.py"
SPEC = importlib.util.spec_from_file_location("jev_compare_validation", MODULE_PATH)
assert SPEC and SPEC.loader
comparison = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = comparison
SPEC.loader.exec_module(comparison)


def ranking_row(index: int, score: float, tier: str) -> dict:
    return {
        "reference_rank": index,
        "reference_score": score,
        "reference_tier": tier,
        "title": f"Reference {index}",
        "pmid": str(1000 + index),
    }


def key(row: dict) -> str:
    from hashlib import sha256
    return sha256(canonical_identity(row).encode("utf-8")).hexdigest()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def test_template_joins_by_canonical_key_and_leaves_human_columns_blank(tmp_path: Path) -> None:
    ranking = [ranking_row(1, 90, "A"), ranking_row(2, 60, "B")]
    shadow = [
        {
            "reference_key_sha256": key(ranking[0]),
            "reference_title": "Reference 1",
            "document_type": "randomized_trial",
            "document_type_confidence": 0.9,
            "nutrition_relevance_score": 4,
        }
    ]
    ranking_path = tmp_path / "ranking.jsonl"
    shadow_path = tmp_path / "shadow.jsonl"
    template_path = tmp_path / "labels.csv"
    write_jsonl(ranking_path, ranking)
    write_jsonl(shadow_path, shadow)
    before = ranking_path.read_bytes()

    manifest = comparison.prepare_template(ranking_path, shadow_path, template_path)
    with template_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert manifest["status"] == "HUMAN_LABEL_TEMPLATE_READY"
    assert rows[0]["nutev_reference_score"] == "90"
    assert rows[0]["jev_document_type"] == "randomized_trial"
    assert rows[0]["human_document_type"] == ""
    assert rows[0]["human_nutrition_relevance"] == ""
    assert ranking_path.read_bytes() == before


def test_analysis_computes_direct_jev_metrics_and_exploratory_nutev_association(tmp_path: Path) -> None:
    ranking = [
        ranking_row(1, 90, "A"),
        ranking_row(2, 70, "B"),
        ranking_row(3, 50, "C"),
    ]
    shadow = [
        {
            "reference_key_sha256": key(ranking[0]),
            "reference_title": "Reference 1",
            "document_type": "randomized_trial",
            "document_type_confidence": 0.9,
            "nutrition_relevance_score": 4.0,
        },
        {
            "reference_key_sha256": key(ranking[1]),
            "reference_title": "Reference 2",
            "document_type": "cohort",
            "document_type_confidence": 0.8,
            "nutrition_relevance_score": 2.5,
        },
        {
            "reference_key_sha256": key(ranking[2]),
            "reference_title": "Reference 3",
            "document_type": "commentary",
            "document_type_confidence": 0.7,
            "nutrition_relevance_score": 1.0,
        },
    ]
    ranking_path = tmp_path / "ranking.jsonl"
    shadow_path = tmp_path / "shadow.jsonl"
    labels_path = tmp_path / "labels.csv"
    output_dir = tmp_path / "out"
    write_jsonl(ranking_path, ranking)
    write_jsonl(shadow_path, shadow)

    with labels_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=comparison.TEMPLATE_FIELDS)
        writer.writeheader()
        writer.writerow({
            "reference_key_sha256": key(ranking[0]),
            "human_document_type": "randomized_trial",
            "human_nutrition_relevance": "4",
        })
        writer.writerow({
            "reference_key_sha256": key(ranking[1]),
            "human_document_type": "cross_sectional",
            "human_nutrition_relevance": "3",
        })
        writer.writerow({
            "reference_key_sha256": key(ranking[2]),
            "human_document_type": "commentary",
            "human_nutrition_relevance": "1",
        })

    before_ranking = ranking_path.read_bytes()
    before_shadow = shadow_path.read_bytes()
    report = comparison.analyze(ranking_path, shadow_path, labels_path, output_dir)

    assert report["status"] == "COMPARISON_COMPLETE"
    assert report["validation_claim"] == "NOT_ESTABLISHED"
    assert report["scientific_effect"] == "none"
    assert report["ranking_effect"] == "none"
    assert report["sample"]["joined_rows"] == 3
    assert report["jev_vs_human"]["document_type"]["exact_accuracy"] == 0.6667
    assert report["jev_vs_human"]["nutrition_relevance"]["mae_0_to_4"] == 0.1667
    assert report["nutev_vs_human_exploratory"]["reference_score_spearman_with_human_relevance"] == 1.0
    assert ranking_path.read_bytes() == before_ranking
    assert shadow_path.read_bytes() == before_shadow
    assert (output_dir / "JEV_COMPARISON_REPORT.json").is_file()
    assert (output_dir / "JEV_COMPARISON_REPORT.md").is_file()


def test_invalid_human_labels_do_not_become_scientific_decisions(tmp_path: Path) -> None:
    ranking = [ranking_row(1, 90, "A")]
    shadow = [{
        "reference_key_sha256": key(ranking[0]),
        "document_type": "randomized_trial",
        "nutrition_relevance_score": 4,
    }]
    ranking_path = tmp_path / "ranking.jsonl"
    shadow_path = tmp_path / "shadow.jsonl"
    labels_path = tmp_path / "labels.csv"
    write_jsonl(ranking_path, ranking)
    write_jsonl(shadow_path, shadow)

    with labels_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=comparison.TEMPLATE_FIELDS)
        writer.writeheader()
        writer.writerow({
            "reference_key_sha256": key(ranking[0]),
            "human_document_type": "included",
            "human_nutrition_relevance": "99",
        })

    report = comparison.analyze(ranking_path, shadow_path, labels_path, tmp_path / "out")
    assert report["status"] == "NEEDS_HUMAN_LABELS"
    assert report["sample"]["joined_rows"] == 0
    assert report["sample"]["invalid_rows"] == 2
    assert report["interpretation_contract"]["no_eligibility_or_prisma_inference"] is True
