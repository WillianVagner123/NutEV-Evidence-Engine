from pathlib import Path
from nutev.global_watch.watch_webhook import build_webhook_payload, maybe_send_webhook, send_webhook
from nutev.settings import NutevSettings
from nutev.logs import setup_logger


def _s(tmp_path):
    s=NutevSettings(project_root=tmp_path)
    for d in s.output_dirs.values(): d.mkdir(parents=True, exist_ok=True)
    return s


def test_payload_has_full_summary_and_top_items():
    p=build_webhook_payload([{"title":"guideline x","download_status":"pdf","watch_score":90}],Path('d.md'),{"mode":"quick","total_items":1,"new_items":1,"high_priority":1,"pdf":1,"html_snapshot":0,"metadata_only":0,"failed":0})
    assert 'summary' in p and 'top_items' in p and p['top_items']


def test_webhook_disabled_skips(tmp_path):
    s=_s(tmp_path)
    r=maybe_send_webhook([],Path(tmp_path/'d.md'),{"mode":"quick"},s,setup_logger(s.output_dirs['07_logs']),'run1',False,None)
    assert r['status']=='skipped'


def test_missing_url_skips(tmp_path):
    s=_s(tmp_path)
    r=maybe_send_webhook([],Path(tmp_path/'d.md'),{"mode":"quick"},s,setup_logger(s.output_dirs['07_logs']),'run1',True,None)
    assert r['status']=='skipped'


def test_requests_post_mock_works(monkeypatch,tmp_path):
    class R: status_code=200
    monkeypatch.setattr('requests.post', lambda *a, **k: R())
    s=_s(tmp_path)
    r=send_webhook({'a':1},'https://example.com/hook',setup_logger(s.output_dirs['07_logs']),'run1',s.output_dirs['07_logs'])
    assert r['status']=='sent'


def test_webhook_failure_not_break(monkeypatch,tmp_path):
    monkeypatch.setattr('requests.post', lambda *a, **k: (_ for _ in ()).throw(RuntimeError('x')))
    s=_s(tmp_path)
    r=maybe_send_webhook([],Path(tmp_path/'d.md'),{"mode":"quick"},s,setup_logger(s.output_dirs['07_logs']),'run1',True,'https://example.com/hook')
    assert r['status']=='failed'
