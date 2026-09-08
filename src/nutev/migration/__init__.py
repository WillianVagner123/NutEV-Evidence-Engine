"""Read-only planning utilities for legacy-to-platform migrations."""

from .legacy_plan import (
    MIGRATION_MANIFEST_SCHEMA_VERSION,
    MIGRATABLE_PRIVATE_CLASSES,
    ExplicitMappingDocument,
    LogicalTarget,
    MappingRule,
    MigrationPlan,
    OwnershipClass,
    load_explicit_mapping,
    run_legacy_multitenant_dry_run,
)

__all__ = [
    "MIGRATION_MANIFEST_SCHEMA_VERSION",
    "MIGRATABLE_PRIVATE_CLASSES",
    "ExplicitMappingDocument",
    "LogicalTarget",
    "MappingRule",
    "MigrationPlan",
    "OwnershipClass",
    "load_explicit_mapping",
    "run_legacy_multitenant_dry_run",
]
