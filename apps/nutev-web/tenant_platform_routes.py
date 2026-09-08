from __future__ import annotations

from tenant_application_api import install_application_routes
from tenant_library_api import install_library_routes


def install_tenant_platform_routes() -> None:
    """Install authenticated platform extensions without coupling them to scientific handlers."""
    install_library_routes()
    install_application_routes()
