from __future__ import annotations

PREGNANCY_GESTATIONAL_PENALTIES: tuple[tuple[str, float], ...] = (
    ("pregnancy", -15.0),
    ("pregnant", -15.0),
    ("gestational", -15.0),
    ("gestational diabetes", -25.0),
    ("maternal obesity", -15.0),
    ("antenatal", -12.0),
    ("prenatal", -12.0),
    ("postpartum", -10.0),
)


def apply_watch_precision_extensions() -> None:
    from nutev.global_watch import watch_scoring

    existing_terms = {term for term, _ in watch_scoring.PENALTY_TERMS}
    additions = tuple(
        item for item in PREGNANCY_GESTATIONAL_PENALTIES if item[0] not in existing_terms
    )
    if additions:
        watch_scoring.PENALTY_TERMS = tuple(watch_scoring.PENALTY_TERMS) + additions
