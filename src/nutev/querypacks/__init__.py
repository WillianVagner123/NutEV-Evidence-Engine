from __future__ import annotations

from nutev.querypacks.adherence_engagement_extensions import (
    apply_adherence_engagement_extensions,
)
from nutev.querypacks.carbohydrate_quality_extensions import (
    apply_carbohydrate_quality_extensions,
)
from nutev.querypacks.food_access_extensions import apply_food_access_benefit_extensions
from nutev.querypacks.group_visit_care_extensions import apply_group_visit_care_extensions
from nutev.querypacks.iberoamerican_guidance_extensions import (
    apply_iberoamerican_guidance_extensions,
)
from nutev.querypacks.portfolio_lipid_extensions import apply_portfolio_lipid_extensions
from nutev.querypacks.semantic_extensions import apply_semantic_extensions

apply_semantic_extensions()
apply_adherence_engagement_extensions()
apply_carbohydrate_quality_extensions()
apply_food_access_benefit_extensions()
apply_group_visit_care_extensions()
apply_iberoamerican_guidance_extensions()
apply_portfolio_lipid_extensions()

__all__ = [
    "apply_adherence_engagement_extensions",
    "apply_carbohydrate_quality_extensions",
    "apply_food_access_benefit_extensions",
    "apply_group_visit_care_extensions",
    "apply_iberoamerican_guidance_extensions",
    "apply_portfolio_lipid_extensions",
    "apply_semantic_extensions",
]
