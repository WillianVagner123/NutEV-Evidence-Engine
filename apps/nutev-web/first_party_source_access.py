"""Server-managed access boundary for the existing private A1 source.

These opaque IDs are populated ONLY from reviewed runtime ownership evidence.
They are not inferred from a username, application configuration, or a directory.
Missing configuration denies access; no ownership record or scientific decision
is created by this helper. A2 keeps its separate LegacyBindingEvidence gate.
"""
from __future__ import annotations

import os
from nutev.tenancy import require_opaque_id


def article1_source_owner_allowed(workspace_id: str, project_id: str) -> bool:
    owner_workspace = os.environ.get('NUTEV_A1_WORKSPACE_ID', '')
    owner_project = os.environ.get('NUTEV_A1_PROJECT_ID', '')
    try:
        require_opaque_id(owner_workspace, 'workspace')
        require_opaque_id(owner_project, 'project')
    except ValueError:
        return False
    return workspace_id == owner_workspace and project_id == owner_project
