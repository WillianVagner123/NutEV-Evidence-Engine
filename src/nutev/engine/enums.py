from __future__ import annotations

from enum import Enum


class EventKind(str, Enum):
    state = "state"
    progress = "progress"
    warning = "warning"
    error = "error"
    metric = "metric"


class DownloadStatus(str, Enum):
    pdf = "pdf"
    html_snapshot = "html_snapshot"
    metadata_only = "metadata_only"
    failed = "failed"
