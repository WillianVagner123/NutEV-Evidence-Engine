from __future__ import annotations

import os

from article1_d132_api import install_article1_d132_routes
from tenant_application_api import install_application_routes
from tenant_library_api import install_library_routes


def _article2_enabled() -> bool:
    return str(os.environ.get("NUTEV_ARTICLE2_ENABLED") or "").strip().casefold() in {
        "1",
        "true",
        "yes",
        "on",
    }


def install_tenant_platform_routes() -> None:
    """Install tenant-platform extensions without coupling them to the scientific Engine."""
    install_library_routes()
    install_application_routes()
    install_article1_d132_routes()

    # Article 2 remains dark-launched until the historical ownership binding is
    # explicitly validated. Keep even the module import lazy so default runtime
    # preserves the already-proven handler chain byte-for-byte at installation time.
    if _article2_enabled():
        from article2_integrative_api import install_article2_integrative_routes

        install_article2_integrative_routes()
