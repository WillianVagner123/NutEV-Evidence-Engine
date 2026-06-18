from __future__ import annotations

from nutev.querypacks import provider_queries

PUBMED_MESH_EXTENSIONS = {
    "abdominal obesity": "Obesity, Abdominal",
    "body mass index": "Body Mass Index",
    "bmi": "Body Mass Index",
    "central obesity": "Obesity, Abdominal",
    "diet quality": "Healthy Diet",
    "diabetes prevention program": "Diabetes Prevention",
    "food insecurity": "Food Insecurity",
    "food security": "Food Security",
    "health equity": "Health Equity",
    "healthy diet": "Healthy Diet",
    "healthy eating": "Healthy Diet",
    "intermittent fasting": "Intermittent Fasting",
    "ketogenic diet": "Diet, Ketogenic",
    "low carbohydrate diet": "Diet, Carbohydrate-Restricted",
    "low-carbohydrate diet": "Diet, Carbohydrate-Restricted",
    "meal replacement": "Meal Replacement Therapy",
    "meal replacements": "Meal Replacement Therapy",
    "social determinants of health": "Social Determinants of Health",
    "sustainable diet": "Sustainable Diet",
    "sustainable diets": "Sustainable Diet",
    "time restricted eating": "Fasting",
    "time-restricted eating": "Fasting",
    "ultra processed food": "Ultra-Processed Foods",
    "ultra processed foods": "Ultra-Processed Foods",
    "ultra-processed food": "Ultra-Processed Foods",
    "ultra-processed foods": "Ultra-Processed Foods",
    "waist circumference": "Waist Circumference",
}

PROVIDER_GUIDANCE_EXTENSIONS = [
    "medical nutrition therapy guideline",
    "nutrition care pathway guideline",
    "nutrition care protocol guideline",
    "nutrition care consensus",
]

BEHAVIOR_PRIORITY_EXTENSIONS = [
    "nutrition care pathway",
    "nutrition care pathways",
    "nutrition care protocol",
    "nutrition care protocols",
    "dietary self-monitoring",
    "dietary self-regulation",
    "eating self-regulation",
]


def _extend_unique(existing: list[str], additions: list[str]) -> None:
    seen = {item.lower() for item in existing}
    for item in additions:
        value = item.strip()
        if not value or value.lower() in seen:
            continue
        existing.append(value)
        seen.add(value.lower())


def apply_provider_mesh_extensions() -> None:
    provider_queries.PUBMED_MESH_MAP.update(PUBMED_MESH_EXTENSIONS)
    _extend_unique(
        provider_queries.BUSCA2A_GUIDANCE_TERMS,
        PROVIDER_GUIDANCE_EXTENSIONS,
    )
    _extend_unique(
        provider_queries.BEHAVIOR_PRIORITY_TERMS,
        BEHAVIOR_PRIORITY_EXTENSIONS,
    )


apply_provider_mesh_extensions()
