from pathlib import Path
from nutev.querypacks.builders import build_querypack
from nutev.download.naming import build_filename, infer_ext
from nutev.download.filters import should_download
from nutev.analysis.relevance import score_record
from nutev.extract.html_text import extract_html_text
from nutev.export.metadata_tables import write_metadata_csv


def test_querypack_builder():
    qp = build_querypack({"workstreams":{"busca1":{"base_terms":["obesity"],"themes":["guideline"]}}}, ["busca1"])
    assert qp["busca1"][0] == '"obesity" AND "guideline"'

def test_naming_and_ext():
    fn = build_filename("busca1","pubmed","My Title","https://x.org/a.pdf","pdf")
    assert fn.startswith("NTV__busca1__") and fn.endswith(".pdf")
    assert infer_ext("https://x.org/noext", "application/pdf") == "pdf"

def test_filters():
    assert should_download("https://site.org/guideline-report.html", "html")
    assert not should_download("https://site.org/login", "html")

def test_scoring():
    r=score_record({"title":"obesity guideline","source":"pubmed"},{"keyword_points":{"obesity":2,"guideline":3},"source_points":{"pubmed":1},"workstream_points":{"busca1":1}},"busca1")
    assert r["relevance_score"] >= 7

def test_html_extract_and_export(tmp_path: Path):
    d=extract_html_text("<html><title>T</title><h1>H</h1><p>Body</p></html>")
    assert d["title"]=="T" and "Body" in d["body"]
    out=tmp_path/"meta.csv"
    write_metadata_csv([{"a":1,"b":2}], out)
    assert out.exists()
