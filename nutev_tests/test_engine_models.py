from datetime import datetime, timezone

from nutev.engine.models import DownloadResult, ProviderHit


def test_providerhit_accepts_minimal_data():
    hit = ProviderHit(provider="pubmed", query="omega 3", title="T", url="https://x")
    assert hit.provider == "pubmed"


def test_downloadresult_accepts_metadata_only():
    r = DownloadResult(document_id="doc_1", status="metadata_only", created_at=datetime.now(timezone.utc))
    assert r.status == "metadata_only"
