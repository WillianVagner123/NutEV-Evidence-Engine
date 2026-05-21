from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

SETTINGS_FILE = "provider_settings.local.json"


def _settings_path(project_root: Path) -> Path:
    return project_root / "00_settings" / SETTINGS_FILE


def load_provider_registry(config_root: Path) -> dict:
    p = config_root / "provider_registry.json"
    if not p.exists():
        return {"providers": []}
    return json.loads(p.read_text(encoding="utf-8"))


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 6:
        return "*" * len(value)
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


def load_provider_settings(project_root: Path) -> dict:
    p = _settings_path(project_root)
    if not p.exists():
        return {"providers": {}}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"providers": {}}
    return validate_provider_settings(data)


def validate_provider_settings(settings: dict) -> dict:
    out = {"providers": {}}
    providers = settings.get("providers", {}) if isinstance(settings, dict) else {}
    for pid, cfg in providers.items():
        if not isinstance(cfg, dict):
            continue
        out["providers"][pid] = {
            "enabled": bool(cfg.get("enabled", False)),
            "mode": str(cfg.get("mode", "disabled")),
            "model": str(cfg.get("model", "")),
            "secret_source": str(cfg.get("secret_source", "env")),
            "env_var": str(cfg.get("env_var", "")),
            "base_url": str(cfg.get("base_url", "")),
            "local_only": bool(cfg.get("local_only", False)),
            **({"api_key": str(cfg.get("api_key", ""))} if cfg.get("api_key") else {}),
        }
    return out


def save_provider_settings(project_root: Path, settings: dict) -> None:
    clean = validate_provider_settings(settings)
    p = _settings_path(project_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_provider_secret(provider_id: str, env_var: str, project_root: Path) -> str | None:
    if env_var and os.getenv(env_var):
        return os.getenv(env_var)
    local = load_provider_settings(project_root)
    cfg = local.get("providers", {}).get(provider_id, {})
    key = cfg.get("api_key")
    if key and cfg.get("local_only", False):
        return str(key)
    return None


def masked_provider_settings(project_root: Path) -> dict[str, Any]:
    data = load_provider_settings(project_root)
    for cfg in data.get("providers", {}).values():
        if cfg.get("api_key"):
            cfg["api_key"] = mask_secret(str(cfg.get("api_key")))
    return data
