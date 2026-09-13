import json

from tools.recovery_snapshot import _snapshot_heartbeat


class _StopAfterOneHeartbeat:
    def __init__(self) -> None:
        self.calls = 0

    def wait(self, interval_seconds: float) -> bool:
        assert interval_seconds == 0
        self.calls += 1
        return self.calls > 1


def test_snapshot_heartbeat_is_periodic_sanitized_json(capsys) -> None:
    stop = _StopAfterOneHeartbeat()
    _snapshot_heartbeat(stop, interval_seconds=0)
    output = capsys.readouterr().out.strip()
    assert stop.calls == 2
    assert json.loads(output) == {"event": "snapshot_progress", "status": "RUNNING"}
    assert "/" not in output
    assert "snapshot-source" not in output
    assert "snapshot-backups" not in output
