from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = REPO_ROOT / "apps" / "nutev-web"
if str(WEB_ROOT) not in sys.path:
    sys.path.insert(0, str(WEB_ROOT))

import progress_search
import search_fulltext


def _rows(count: int = 4) -> list[dict]:
    return [
        {
            "title": f"Article {index}",
            "pmcid": f"PMC{1000 + index}",
            "reference_rank": index,
            "reference_score": float(100 - index),
        }
        for index in range(1, count + 1)
    ]


def test_selective_enrichment_is_bounded_and_never_changes_rank(monkeypatch, tmp_path: Path) -> None:
    calls: list[int] = []

    def fake_enrich(row: dict, *, output_root: Path, allow_network: bool) -> dict:
        calls.append(int(row["reference_rank"]))
        return {
            "status": "extracted",
            "ocr_used": row["reference_rank"] == 2,
            "cache_hit": False,
            "text_chars": 1200,
            "ranking_influence": "none",
        }

    monkeypatch.setattr(search_fulltext, "_enrich_one", fake_enrich)
    rows = _rows()
    original = [(row["reference_rank"], row["reference_score"]) for row in rows]

    enriched, summary = search_fulltext.enrich_ranked_results(
        rows,
        output_root=tmp_path,
        search_id="web_test",
        limit=2,
        allow_network=True,
    )

    assert calls == [1, 2]
    assert [(row["reference_rank"], row["reference_score"]) for row in enriched] == original
    assert enriched[0]["full_text"]["status"] == "extracted"
    assert enriched[1]["full_text"]["ocr_used"] is True
    assert enriched[2]["full_text"]["status"] == "candidate_available_not_processed"
    assert summary["selected"] == 2
    assert summary["extracted"] == 2
    assert summary["ocr_used"] == 1
    assert summary["ranking_unchanged"] is True
    assert summary["public_payload_contains_full_text"] is False


def test_enrichment_failure_is_recorded_without_failing_search(monkeypatch, tmp_path: Path) -> None:
    def explode(*_args, **_kwargs):
        raise RuntimeError("synthetic extraction failure")

    monkeypatch.setattr(search_fulltext, "_enrich_one", explode)
    rows = _rows(1)

    enriched, summary = search_fulltext.enrich_ranked_results(
        rows,
        output_root=tmp_path,
        search_id="web_test",
        limit=1,
        allow_network=True,
    )

    meta = enriched[0]["full_text"]
    assert meta["status"] == "failed"
    assert "synthetic extraction failure" in meta["error"]
    assert enriched[0]["reference_rank"] == 1
    assert enriched[0]["reference_score"] == 99.0
    assert summary["failed"] == 1


def test_extracted_text_is_private_and_second_read_uses_cache(monkeypatch, tmp_path: Path) -> None:
    row = _rows(1)[0]
    candidate = {
        "url": "https://example.org/article.pdf",
        "scope": "full_text",
        "media_type": "application/pdf",
        "resolver_route": "test_pdf",
        "resolver_source": "test",
    }
    monkeypatch.setattr(
        search_fulltext,
        "_full_text_candidates",
        lambda _row, *, allow_network: [candidate],
    )
    monkeypatch.setattr(
        search_fulltext,
        "select_reachable_candidate",
        lambda candidates, **_kwargs: ({**candidates[0], "probe_selected": True}, [{"reachable": True}]),
    )

    downloaded = tmp_path / "source.pdf"
    downloaded.write_bytes(b"%PDF synthetic")
    download_calls = {"count": 0}

    def fake_download(_url: str, _target: Path):
        download_calls["count"] += 1
        return downloaded, "application/pdf", "https://example.org/article.pdf"

    monkeypatch.setattr(search_fulltext, "_download", fake_download)
    monkeypatch.setattr(
        search_fulltext,
        "_extract_local_file",
        lambda _path, _media: (
            "full text body " * 100,
            SimpleNamespace(value="ocr_tesseract"),
            True,
            "tesseract",
            [],
        ),
    )
    monkeypatch.setattr(
        search_fulltext,
        "_section_blocks",
        lambda _text, _document_id: (SimpleNamespace(heading="Methods"), SimpleNamespace(heading="Results")),
    )
    monkeypatch.setattr(
        search_fulltext,
        "_content_signals",
        lambda _text, _blocks: {"study_design_signals": ["randomized controlled trial"]},
    )

    first = search_fulltext._enrich_one(row, output_root=tmp_path, allow_network=True)
    assert first["status"] == "extracted"
    assert first["ocr_used"] is True
    assert first["cache_hit"] is False
    assert "private_text_file" not in first
    assert "private_text_sha256" not in first
    assert "text" not in first

    monkeypatch.setattr(
        search_fulltext,
        "_download",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("cache should skip download")),
    )
    second = search_fulltext._enrich_one(row, output_root=tmp_path, allow_network=True)
    assert second["status"] == "extracted"
    assert second["cache_hit"] is True
    assert second["ocr_used"] is True
    assert download_calls["count"] == 1
    assert list((tmp_path / "16_search_full_text_cache").rglob("private-text.txt"))


def test_configured_budget_defaults_off_and_is_clamped(monkeypatch) -> None:
    monkeypatch.delenv("NUTEV_SEARCH_FULLTEXT_LIMIT", raising=False)
    assert search_fulltext.configured_full_text_limit() == 0
    monkeypatch.setenv("NUTEV_SEARCH_FULLTEXT_LIMIT", "999")
    assert search_fulltext.configured_full_text_limit() == search_fulltext.MAX_AUTO_FULL_TEXT
    monkeypatch.setenv("NUTEV_SEARCH_FULLTEXT_LIMIT", "invalid")
    assert search_fulltext.configured_full_text_limit() == 0


def test_progressive_wrapper_persists_enriched_result_without_touching_scientific_state(monkeypatch, tmp_path: Path) -> None:
    base = {
        "search_id": "web_test",
        "results": _rows(2),
        "interactive_limitations": [],
        "status": "COMPLETE",
    }
    monkeypatch.setenv("NUTEV_SEARCH_FULLTEXT_LIMIT", "2")
    monkeypatch.setattr(progress_search, "_search_without_full_text", lambda *_args, **_kwargs: dict(base))
    persisted: list[dict] = []
    monkeypatch.setattr(progress_search, "_persist_search", lambda result, _root: persisted.append(result))

    def fake_enrich(rows, **_kwargs):
        rows[0]["full_text"] = {"status": "extracted", "ranking_influence": "none"}
        return rows, {
            "enabled": True,
            "status": "completed",
            "selected": 2,
            "extracted": 1,
            "ocr_used": 0,
            "ranking_unchanged": True,
            "public_payload_contains_full_text": False,
        }

    monkeypatch.setattr(search_fulltext, "enrich_ranked_results", fake_enrich)
    result = progress_search.search_evidence_progressive(
        "nutrition",
        output_root=tmp_path,
    )

    assert result["full_text_enrichment"]["status"] == "completed"
    assert result["results"][0]["full_text"]["status"] == "extracted"
    assert persisted and persisted[-1] is result
    assert "formal_provider_search_executed" not in result
    assert "prisma_search_event_emitted" not in result


def test_production_image_enables_small_budget_and_ocr_dependencies() -> None:
    dockerfile = (REPO_ROOT / "deploy" / "hetzner" / "Dockerfile").read_text(encoding="utf-8")
    assert "NUTEV_SEARCH_FULLTEXT_LIMIT=3" in dockerfile
    assert "NUTEV_OCR_LANG=eng+por" in dockerfile
    assert "poppler-utils" in dockerfile
    assert "tesseract-ocr-eng" in dockerfile
    assert "tesseract-ocr-por" in dockerfile


def test_full_text_ui_is_connected_to_central_search_event_bus() -> None:
    events = (WEB_ROOT / "search-events.js").read_text(encoding="utf-8")
    ui = (WEB_ROOT / "search-fulltext-ui.js").read_text(encoding="utf-8")
    assert "import'./search-fulltext-ui.js'" in events
    assert "window.fetch=" not in ui
    assert "nutev:search-result" in ui
    assert "OCR aplicado" in ui
    assert "não altera o ranking" in ui
