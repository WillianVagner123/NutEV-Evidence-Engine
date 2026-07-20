"""Phase-0 parity harness for the runtime_compat migration.

Gate for `docs/REFACTOR_RUNTIME_COMPAT_MIGRATION.md`. It locks the *exact* queries
the pipeline generates today (runtime_compat patches applied) as a committed
digest baseline. As the migration moves query terms out of
`_patch_query_generation` into `querypacks/`, this test must stay green —
identical digests prove the generated queries never changed (same input → same
output). A changed digest means a phase altered scientific output and must be
reviewed before merge.

The signature is computed in a FRESH subprocess (see
`parity/gen_runtime_compat_signature.py`) so the measurement is hermetic — it
reflects the pipeline's real patched behaviour and cannot be perturbed by global
patch/module state left behind by other tests in the same pytest session.

To regenerate the baseline (ONLY with an intentional, documented decision):
    python nutev_tests/parity/gen_runtime_compat_signature.py > \
        nutev_tests/parity/runtime_compat_query_baseline.json
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[1]
_GEN = _HERE.parent / "parity" / "gen_runtime_compat_signature.py"
_BASELINE = _HERE.parent / "parity" / "runtime_compat_query_baseline.json"


def _run_generator() -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = "src" + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [sys.executable, str(_GEN)],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
        env=env,
    )
    assert proc.returncode == 0, f"generator failed:\n{proc.stderr}"
    return json.loads(proc.stdout)


def _strip(sig: dict) -> dict:
    return {k: v for k, v in sig.items() if k != "_comment"}


def test_generated_queries_match_the_committed_baseline():
    baseline = json.loads(_BASELINE.read_text(encoding="utf-8"))
    current = _run_generator()

    # Field-by-field so a failure localizes exactly which workstream/provider drifted.
    for ws in baseline["workstreams"]:
        assert current["general"][ws] == baseline["general"][ws], f"general querypack drifted: {ws}"
        for prov in baseline["providers"]:
            assert current["provider"][ws][prov] == baseline["provider"][ws][prov], (
                f"provider querypack drifted: {ws}/{prov}"
            )
    assert current["overall_sha256"] == baseline["overall_sha256"], "overall query digest drifted"
    # Full structural equality (minus the human-readable comment).
    assert _strip(current) == _strip(baseline)


def test_query_generation_is_deterministic():
    # The harness itself must be stable across fresh processes, or it gates nothing.
    assert _strip(_run_generator()) == _strip(_run_generator())
