from __future__ import annotations

def apply_domain_rules(records: list[dict], rules: dict) -> list[dict]:
    keys = rules.get("domains", {})
    for r in records:
        txt = ((r.get("extracted_text") or r.get("title") or "")).lower()
        for domain, terms in keys.items():
            c = sum(1 for t in terms if t.lower() in txt)
            r[f"domain_{domain}_count"] = c
            r[f"domain_{domain}_present"] = int(c > 0)
    return records
