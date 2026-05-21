from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from nutev.api.routes import build_router


def create_app(project_root: Path) -> FastAPI:
    app = FastAPI(title="NutEV Platform", description="Local NutEV Platform API", version="0.1.0")
    app.include_router(build_router(project_root))
    return app
