"""Explicit first-party migration profiles kept outside the reusable scientific core."""

from .willian_doctorate import WILLIAN_DOCTORATE_PLAN_ID, build_willian_doctorate_plan

FIRST_PARTY_DOCTORATE_PROFILE = "first-party-doctorate-v1"


def get_migration_profile(name: str):
    key = str(name or "").strip().casefold()
    if key == FIRST_PARTY_DOCTORATE_PROFILE:
        return build_willian_doctorate_plan()
    raise KeyError(f"unknown migration profile: {name}")


__all__ = [
    "FIRST_PARTY_DOCTORATE_PROFILE",
    "WILLIAN_DOCTORATE_PLAN_ID",
    "build_willian_doctorate_plan",
    "get_migration_profile",
]
