from nutev.engine.ids import make_run_id
from nutev.engine.job import create_search_case, create_search_job, write_search_job_snapshot


def test_search_job_snapshot_created(tmp_path):
    case = create_search_case("n", ["busca1"], "thesis", ["pubmed"])
    job = create_search_job(case.case_id, make_run_id(), ["--x"])
    out = tmp_path / "search_job_snapshot.json"
    write_search_job_snapshot(job, out, {"mode": "thesis", "workstreams": ["busca1"]})
    assert out.exists()
