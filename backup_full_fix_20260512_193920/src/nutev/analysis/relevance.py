from __future__ import annotations


def score_record(record: dict, scoring_rules: dict, workstream: str) -> dict:
    score = 0
    title = (record.get("title") or "").lower()
    for kw, points in scoring_rules.get("keyword_points", {}).items():
        if kw.lower() in title:
            score += points
    score += scoring_rules.get("source_points", {}).get(record.get("source"), 0)
    score += scoring_rules.get("workstream_points", {}).get(workstream, 0)
    record["relevance_score"] = score
    return record
