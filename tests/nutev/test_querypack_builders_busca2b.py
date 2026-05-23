from __future__ import annotations

import json
from pathlib import Path

from nutev.querypacks.builders import build_queries


def _load_keyword_taxonomy() -> dict:
    repo_root = Path(__file__).resolve().parents[2]
    return json.loads((repo_root / "config" / "keyword_taxonomy.json").read_text(encoding="utf-8"))


def test_busca2b_queries_include_implementation_delivery_terms() -> None:
    taxonomy = _load_keyword_taxonomy()

    queries = build_queries(taxonomy, "busca2b")
    joined = "\n".join(queries).lower()

    assert "implementation trial" in joined
    assert "quality improvement" in joined
    assert "real-world implementation" in joined or "real world implementation" in joined
    assert "audit and feedback" in joined
