"""The human-review worksheet for config/query_vocabulary.json stays in sync and never
claims a human review it did not receive."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import review_query_vocabulary as review  # noqa: E402


def test_worksheet_and_report_match_the_vocabulary() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "review_query_vocabulary.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_worksheet_has_one_row_per_concept_and_empty_decisions() -> None:
    vocabulary = json.loads((ROOT / "config" / "query_vocabulary.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader(io.StringIO(review.WORKSHEET_PATH.read_text(encoding="utf-8"))))
    assert [row["concept_id"] for row in rows] == [concept["id"] for concept in vocabulary["concepts"]]
    assert all(row["reviewer_decision"] == "" and row["reviewer_notes"] == "" for row in rows)


def test_pre_review_is_mechanical_and_does_not_approve() -> None:
    vocabulary = json.loads((ROOT / "config" / "query_vocabulary.json").read_text(encoding="utf-8"))
    assert vocabulary["review_status"] == "curated_pending_human_review"
    source = (ROOT / "tools" / "review_query_vocabulary.py").read_text(encoding="utf-8")
    assert "human_reviewed" not in source
    assert "query_vocabulary.json" in source and "write_text" in source
    # The tool writes only into docs/review.
    assert "CONFIG_DIR /" not in source


def test_checks_flag_shadowed_triggers_and_broad_synonyms() -> None:
    vocabulary = {
        "stopwords": {"pt": ["de"]},
        "concepts": [
            {"id": "a.one", "role": "intervention", "taxonomy_group": "g", "triggers": ["kefir"], "en": ["kefir"], "pt": ["kefir"]},
            {"id": "b.two", "role": "intervention", "taxonomy_group": "g", "triggers": ["kefir", "de"], "en": ["diet", "diet"], "pt": []},
        ],
    }
    codes = {(issue["concept_id"], issue["code"]) for issue in review.find_issues(vocabulary)}
    assert ("b.two", "trigger_shadowed") in codes
    assert ("b.two", "broad_single_word") in codes
    assert ("b.two", "duplicate_synonym") in codes
    assert ("b.two", "stopword_trigger") in codes
    assert ("b.two", "no_portuguese_terms") in codes
