"""Actual container recovery rehearsal with different numeric filesystem owner."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sqlite3
import tempfile

from tools.recovery_snapshot import create_snapshot, rehearse_restore


def main() -> None:
    if os.geteuid() != 0:
        raise SystemExit('This disposable container test requires root to verify numeric ownership.')
    with tempfile.TemporaryDirectory(prefix='nutev-container-recovery-') as temp:
        root = Path(temp)
        source = root / 'source'
        source.mkdir()
        (source / 'empty').mkdir()
        (source / 'private.txt').write_text('synthetic only')
        database = source / 'state.sqlite'
        with sqlite3.connect(database) as connection:
            connection.execute('CREATE TABLE decisions(id INTEGER PRIMARY KEY, decision TEXT)')
            connection.execute("INSERT INTO decisions VALUES(1, 'synthetic-human-decision')")
        for path in [source, *source.rglob('*')]:
            os.chown(path, 10001, 10001)
        (source / 'private.txt').chmod(0o600)
        snapshot = create_snapshot(source, root / 'backup', quiesced=True)
        proof = rehearse_restore(root / 'backup', root / 'restore')
        assert proof['databases'][0]['row_counts']['decisions'] == 1
        assert (root / 'restore/private.txt').stat().st_uid == 10001
        assert (root / 'restore/empty').is_dir()
        print(json.dumps({'status': 'PASS', 'snapshot': snapshot,
                          'numeric_ownership_restored': True, 'production_touched': False}))


if __name__ == '__main__':
    main()
