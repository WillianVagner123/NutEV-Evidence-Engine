from nutev.global_watch.watch_capture import capture_watch_items
from nutev.settings import NutevSettings
from nutev.logs import setup_logger


def _s(tmp_path):
    s=NutevSettings(project_root=tmp_path)
    for d in s.output_dirs.values(): d.mkdir(parents=True, exist_ok=True)
    return s


def test_capture_metadata_only_on_bad_url(tmp_path):
    s=_s(tmp_path)
    rows,_=capture_watch_items([{"document_id":"d1","url":"","title":"x"}],s,setup_logger(s.output_dirs['07_logs']),'run1','quick')
    assert rows[0]['download_status']=='metadata_only'


def test_capture_limit_by_mode(tmp_path):
    s=_s(tmp_path)
    items=[{"document_id":f"d{i}","url":""} for i in range(25)]
    _,cap=capture_watch_items(items,s,setup_logger(s.output_dirs['07_logs']),'run1','quick')
    assert len(cap)==10
