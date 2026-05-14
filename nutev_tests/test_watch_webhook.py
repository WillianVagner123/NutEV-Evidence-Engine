from pathlib import Path
from nutev.global_watch.watch_webhook import build_webhook_payload, maybe_send_webhook, send_webhook
from nutev.settings import NutevSettings
from nutev.logs import setup_logger


def _s(tmp_path):
    s=NutevSettings(project_root=tmp_path)
    for d in s.output_dirs.values(): d.mkdir(parents=True, exist_ok=True)
    return s


def test_build_webhook_payload_summary_correct():
    p=build_webhook_payload([{"title":"A","download_status":"pdf"}],Path('d.md'),{"mode":"quick","new_items":1,"total_items":1})
    assert p['project']=='NutMEV Global Watch' and 'text' in p


def test_send_webhook_post_mock(monkeypatch,tmp_path):
    class R: status_code=200
    monkeypatch.setattr('requests.post', lambda *a, **k: R())
    s=_s(tmp_path)
    r=send_webhook({"a":1},'https://example.com/hook',setup_logger(s.output_dirs['07_logs']),'run1',s.output_dirs['07_logs'])
    assert r['status']=='sent'


def test_maybe_send_webhook_skips_disabled(tmp_path):
    s=_s(tmp_path)
    r=maybe_send_webhook([],Path(tmp_path/'d.md'),{"mode":"quick"},s,setup_logger(s.output_dirs['07_logs']),'run1',False,None)
    assert r['status']=='skipped'


def test_maybe_send_webhook_skips_missing_url(tmp_path):
    s=_s(tmp_path)
    r=maybe_send_webhook([],Path(tmp_path/'d.md'),{"mode":"quick"},s,setup_logger(s.output_dirs['07_logs']),'run1',True,None)
    assert r['status']=='skipped'


def test_webhook_failure_not_break(monkeypatch,tmp_path):
    def boom(*a, **k): raise RuntimeError('x')
    monkeypatch.setattr('requests.post', boom)
    s=_s(tmp_path)
    r=maybe_send_webhook([],Path(tmp_path/'d.md'),{"mode":"quick"},s,setup_logger(s.output_dirs['07_logs']),'run1',True,'https://example.com/hook')
    assert r['status']=='failed'
