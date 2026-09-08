from __future__ import annotations

from article1_d132_api import install_article1_d132_routes
from article2_integrative_api import install_article2_integrative_routes
from tenant_application_api import install_application_routes
from tenant_library_api import install_library_routes


def install_tenant_platform_routes() -> None:
    """Install tenant-platform extensions without coupling them to the scientific Engine."""
    install_library_routes()
    install_application_routes()
    install_article1_d132_routes()
    install_article2_integrative_routes()
