from __future__ import annotations

from nutev.download.downloader import download_records


class Logger:
    def info(self, *args, **kwargs):
        pass
    def warning(self, *args, **kwargs):
        pass


def test_download_bad_url_becomes_metadata_only(tmp_path):
    manifest, failed = download_records([{"url": "notaurl", "title": "Bad", "source": "pubmed"}], tmp_path / "p", tmp_path / "o", Logger())
    assert manifest == []
    assert failed
    assert failed[0]["status"] == "metadata_only"
