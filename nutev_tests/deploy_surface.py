"""The production deploy surface spans two files, not one.

The remote half of the Hetzner deploy used to be a heredoc inside
``.github/workflows/deploy-hetzner.yml``. It now lives in
``deploy/hetzner/remote_deploy.sh`` so it can be delivered as a checksum-verified file
rather than streamed into ``bash -s``, where a truncated delivery read as a clean deploy.

Contract tests that assert on deploy *behaviour* must read both files, or they would stop
seeing the logic they exist to guard. Tests asserting on workflow *structure* — step
ordering, artifact upload, triggers — should keep reading the workflow alone.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEPLOY_WORKFLOW = ROOT / ".github" / "workflows" / "deploy-hetzner.yml"
REMOTE_DEPLOY_SCRIPT = ROOT / "deploy" / "hetzner" / "remote_deploy.sh"


def deploy_surface_text() -> str:
    """Workflow plus the remote script it executes, as one searchable body."""
    return (
        DEPLOY_WORKFLOW.read_text(encoding="utf-8")
        + "\n"
        + REMOTE_DEPLOY_SCRIPT.read_text(encoding="utf-8")
    )
