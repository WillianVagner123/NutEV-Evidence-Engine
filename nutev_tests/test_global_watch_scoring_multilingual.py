from __future__ import annotations

from nutev.global_watch.watch_scoring import score_watch_item


def _watch_score(title: str, abstract: str = "") -> float:
    return score_watch_item(
        {
            "title": title,
            "abstract": abstract,
            "source_provider": "pubmed",
            "download_status": "metadata_only",
        }
    )


def test_multilingual_food_literacy_terms_gain_watch_priority() -> None:
    boosted = _watch_score(
        "Literacia alimentar e medicina culinaria para obesidade e risco cardiometabolico",
        "Planejamento de refeicoes, habilidades culinarias e autoeficacia alimentar em adultos",
    )
    baseline = _watch_score(
        "Programa educacional para obesidade e risco cardiometabolico",
        "Intervencao comunitaria generica em adultos",
    )

    assert boosted > baseline


def test_spanish_food_competence_terms_gain_watch_priority() -> None:
    boosted = _watch_score(
        "Alfabetizacion alimentaria y competencias alimentarias en diabetes tipo 2",
        "Planificacion de comidas, agencia alimentaria y adherencia dietaria",
    )
    baseline = _watch_score(
        "Educacion en diabetes tipo 2",
        "Programa general para adherencia dietaria",
    )

    assert boosted > baseline
