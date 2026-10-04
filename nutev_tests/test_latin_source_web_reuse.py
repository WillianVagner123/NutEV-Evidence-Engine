import importlib.util
from pathlib import Path


def _load_latin_module():
    path = Path(__file__).resolve().parents[1] / "tools" / "run_latin_sources.py"
    spec = importlib.util.spec_from_file_location("nutev_test_run_latin_sources", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_latin_runner_can_select_one_provider_without_touching_the_other(monkeypatch, tmp_path: Path) -> None:
    latin = _load_latin_module()
    calls: list[str] = []

    def fake_run(provider: str, search_url: str, query: str, run_dir: Path):
        calls.append(provider)
        records_path = run_dir / "providers" / f"{provider}.jsonl"
        records_path.parent.mkdir(parents=True, exist_ok=True)
        records_path.write_text(
            '{"source":"%s","source_provider":"%s","title":"A sufficiently long synthetic reference title for testing","url":"https://example.org/ref"}\n'
            % (provider, provider),
            encoding="utf-8",
        )
        return {
            "provider": provider,
            "status": "completed",
            "started_at": "2026-08-20T00:00:00-03:00",
            "finished_at": "2026-08-20T00:00:01-03:00",
            "search_url": search_url,
            "query": query,
            "records_path": str(records_path),
            "records": 1,
        }

    monkeypatch.setattr(latin, "_run_provider", fake_run)
    result = latin.run(tmp_path, "dietary patterns", providers=["scielo_native"])

    assert calls == ["scielo_native"]
    assert result["requested_providers"] == ["scielo_native"]
    assert result["records"] == 1
    assert result["failed_providers"] == []
    assert result["unavailable_providers"] == []


def test_native_urls_keep_the_query_as_written_and_use_a_chosen_language() -> None:
    # Audit finding A7: SciELO was always called with lang=en and the query wrapped in
    # subject:(...), which restricted a compiled Boolean string to one field.
    latin = _load_latin_module()
    query = '("dieta mediterrânea" OR "mediterranean diet") AND diabetes'
    scielo = latin.scielo_search_url(query)
    assert "subject" not in scielo and "lang=pt" in scielo
    assert latin.scielo_search_url(query, lang="es").count("lang=es") == 1
    assert "lang=en" in latin.lilacs_search_url(query, lang="en")
    try:
        latin.scielo_search_url(query, lang="fr")
    except ValueError:
        pass
    else:  # pragma: no cover - guard
        raise AssertionError("unsupported language accepted")


def test_runner_records_that_only_the_first_page_was_read(monkeypatch, tmp_path: Path) -> None:
    latin = _load_latin_module()

    class Response:
        status_code = 200
        text = '<a href="https://www.scielo.br/j/example/a/article123/">A sufficiently long synthetic article title for parsing</a>'

        def raise_for_status(self) -> None:
            return None

    monkeypatch.setattr(latin.requests, "get", lambda *args, **kwargs: Response())
    result = latin.run(tmp_path, "nutrition", providers=["scielo_native"], lang="es")
    assert result["interface_language"] == "es"
    assert result["pagination"] == "first_page_only"
    provider = result["providers"][0]
    assert provider["pages_read"] == 1 and provider["pagination"] == "first_page_only"
    assert "lang=es" in provider["search_url"] and "subject" not in provider["search_url"]
