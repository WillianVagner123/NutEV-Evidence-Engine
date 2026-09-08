from __future__ import annotations

from nutev.migration.legacy_plan import (
    LogicalTarget,
    MappingRule,
    MigrationPlan,
    OwnershipClass,
)
from nutev.tenancy.applications import INTEGRATIVE_REVIEW, SCOPING_REVIEW


WILLIAN_DOCTORATE_PLAN_ID = "willian-doctorate-v1"


def build_willian_doctorate_plan() -> MigrationPlan:
    """Return the first-party migration profile; this is migration config, not Engine state."""

    return MigrationPlan(
        plan_id=WILLIAN_DOCTORATE_PLAN_ID,
        owner_label="Willian",
        targets=(
            LogicalTarget(
                key="doctorate_workspace",
                kind="workspace",
                label="Doutorado Willian — UnB",
            ),
            LogicalTarget(
                key="article1_project",
                kind="project",
                label="Artigo 1",
                parent_key="doctorate_workspace",
                application_template=SCOPING_REVIEW,
            ),
            LogicalTarget(
                key="article2_project",
                kind="project",
                label="Artigo 2",
                parent_key="doctorate_workspace",
                application_template=INTEGRATIVE_REVIEW,
            ),
        ),
        rules=(
            MappingRule(
                pattern="agent_context/article1/*",
                classification=OwnershipClass.ARTICLE1_PRIVATE,
                target_key="article1_project",
                evidence=(
                    "PR-0 inventory classifies agent_context/article1/* as ARTICLE1_PRIVATE; "
                    "migration remains reference-only"
                ),
            ),
            MappingRule(
                pattern="scientific/review_routes/*/article1/*",
                classification=OwnershipClass.ARTICLE1_PRIVATE,
                target_key="article1_project",
                evidence=(
                    "PR-0 inventory classifies scientific/review_routes/<search_id>/article1/* "
                    "as ARTICLE1_PRIVATE"
                ),
            ),
            MappingRule(
                pattern="16_validation_server/validation.sqlite3",
                classification=OwnershipClass.WILLIAN_PRIVATE,
                target_key="doctorate_workspace",
                evidence=(
                    "PR-0 inventory classifies validation.sqlite3 as WILLIAN_PRIVATE/project-to-demonstrate; "
                    "do not attach it to A1 or A2 without later explicit evidence"
                ),
            ),
            MappingRule(
                pattern="15_web_searches/.ownership.json",
                classification=OwnershipClass.SYSTEM,
                target_key=None,
                evidence=(
                    "PR-0 inventory identifies browser-session ownership as legacy SYSTEM metadata, "
                    "not scientific identity"
                ),
            ),
        ),
        required_target_keys=("article1_project", "article2_project"),
    )
