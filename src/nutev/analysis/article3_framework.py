from __future__ import annotations

def build_framework_signals(records: list[dict]) -> list[dict]:
    keywords = ["framework", "pyramid", "menu", "competenc", "questionnaire", "adherence"]
    for r in records:
        t=(r.get("extracted_text") or "").lower()
        r["a3_signal_count"] = sum(1 for k in keywords if k in t)
        r["a3_signal_present"] = int(r["a3_signal_count"] > 0)
    return records
