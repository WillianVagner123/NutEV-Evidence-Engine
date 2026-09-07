from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def read(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def test_search_event_bus_is_loaded_before_all_search_consumers() -> None:
    html = read("search.html")

    assert "search-events.js" in html
    assert html.index("search-events.js") < html.index("search-library-ui.js")
    assert html.index("search-events.js") < html.index("search-facets-ui.js")
    assert html.index("search-events.js") < html.index("search-ux-resilience.js")
    assert html.index("search-events.js") < html.index("search-guided-recovery.js")
    assert html.index("search-events.js") < html.index("app.js")


def test_only_event_bus_wraps_window_fetch_in_public_search_extensions() -> None:
    scripts = {
        name: read(name)
        for name in (
            "search-events.js",
            "search-library-ui.js",
            "search-facets-ui.js",
            "search-ux-resilience.js",
            "search-guided-recovery.js",
        )
    }

    assert scripts["search-events.js"].count("window.fetch=") == 1
    for name in (
        "search-library-ui.js",
        "search-facets-ui.js",
        "search-ux-resilience.js",
        "search-guided-recovery.js",
    ):
        assert "window.fetch=" not in scripts[name]


def test_one_response_clone_fans_out_lifecycle_events() -> None:
    events = read("search-events.js")

    assert events.count("response.clone().json()") == 1
    assert "emit('nutev:search-job'" in events
    assert "emit('nutev:search-result'" in events
    assert "emit('nutev:search-failed'" in events
    assert "emit('nutev:search-transport-retry'" in events
    assert "getLastResult:()=>lastResult" in events
    assert "getLastJob:()=>lastJob" in events


def test_retry_remains_fail_safe_and_never_reposts_a_search() -> None:
    events = read("search-events.js")

    assert "RETRYABLE_JOB_STATUS=new Set([408,429,500,502,503,504])" in events
    assert "RETRY_DELAYS=[400,900,1800]" in events
    assert "const isJobRead=meta.method==='GET'&&meta.path.startsWith('/api/search/jobs/')" in events
    assert "isJobRead?await robustJobFetch(args,meta.path):await nativeFetch(...args)" in events
    assert "path==='/api/search/jobs'&&method==='POST'" in events
    assert "robustJobFetch(args,meta.path)" in events


def test_library_facets_and_ux_consume_the_same_result_event() -> None:
    library = read("search-library-ui.js")
    facets = read("search-facets-ui.js")
    ux = read("search-ux-resilience.js")
    recovery = read("search-guided-recovery.js")

    assert "addEventListener('nutev:search-result'" in library
    assert "addEventListener('nutev:search-result'" in facets
    assert "addEventListener('nutev:search-result'" in ux
    assert "addEventListener('nutev:search-result'" in recovery


def test_transport_bus_does_not_acquire_scientific_authority() -> None:
    events = read("search-events.js").casefold()

    for forbidden in (
        "grade",
        "risk of bias",
        "certeza da evidência",
        "recomendação clínica",
        "eligibility",
    ):
        assert forbidden not in events
