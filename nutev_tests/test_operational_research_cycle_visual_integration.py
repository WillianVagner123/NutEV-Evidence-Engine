from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def read(name: str) -> str:
    return (WEB / name).read_text(encoding="utf-8")


def test_radar_strategy_and_quality_wire_shared_operational_cycle() -> None:
    for page in ("radar.html", "strategy.html", "quality.html"):
        html = read(page)
        assert 'src="./operational-cycle.js"' in html

    script = read("operational-cycle.js")
    assert "Evidence Radar" in script
    assert "Strategy Lab" in script
    assert "Quality Observatory" in script
    assert "Observe → Prepare → Verify, sem promoção científica automática" in script
    assert "./operational-cycle.css" in script


def test_cycle_is_navigation_only_and_does_not_add_scientific_io() -> None:
    script = read("operational-cycle.js")

    assert "navigation only" in script
    assert "Radar, Strategy Lab e Quality Observatory são superfícies operacionais distintas" in script
    assert "não aprova query" in script
    assert "PRESS/GF-10" in script
    assert "EvidenceClaim" in script
    assert "PRISMA" in script
    assert "fetch(" not in script
    assert "XMLHttpRequest" not in script
    assert "method:'POST'" not in script
    assert 'method: "POST"' not in script


def test_current_stage_is_not_a_duplicate_navigation_link() -> None:
    script = read("operational-cycle.js")

    assert 'aria-current="step"' in script
    assert 'data-operational-cycle-target' in script
    assert '<a ' not in script
    assert "location.assign" in script


def test_radar_cycle_reuses_existing_controls_and_keeps_gap_semantics() -> None:
    script = read("operational-cycle.js")

    assert "#refreshRadar" in script
    assert "#jumpChanges" in script
    assert "#summaryCards" in script
    assert "Tópicos com gaps" in script
    assert "Busca ativa requerida" in script
    assert "prioridade operacional não é grau de evidência" in script
    assert "não converte gaps, volume, prioridade ou eventos do Watch em termos de busca" in script


def test_strategy_cycle_reflects_canonical_gates_without_approving_them() -> None:
    script = read("operational-cycle.js")

    assert "#strategyReadiness" in script
    assert "PRESS / GF-10" in script
    assert "Freeze / Formal" in script
    assert "#deltaTests" in script
    assert "estado canônico refletido, nunca inferido" in script
    assert "Frequência, gaps e provider status não promovem termos" in script
    assert "dependentes dos contratos canônicos existentes" in script


def test_quality_cycle_is_system_observability_not_evidence_quality() -> None:
    script = read("operational-cycle.js")

    assert "#qualityHealth" in script
    assert "#qualityKpis" in script
    assert "#refreshQuality" in script
    assert "Full-text coverage" in script
    assert "Saúde do sistema, integridade e completude técnica" in script
    assert "não é avaliação metodológica da evidência" in script
    assert "Quality Observatory não autoriza Strategy" in script
    assert "não produz evidence-quality score" in script
    assert "Erro de provider significa indisponibilidade operacional" in script


def test_operational_cycle_is_responsive_and_keyboard_native() -> None:
    script = read("operational-cycle.js")
    styles = read("operational-cycle.css")

    assert '<button type="button" class="operational-cycle-stage"' in script
    assert '<button type="button" class="operational-cycle-action' in script
    assert "@media(max-width:900px)" in styles
    assert "@media(max-width:640px)" in styles
    assert ":focus-visible" in styles


def test_visual_cycle_does_not_hardcode_production_snapshot_counts() -> None:
    script = read("operational-cycle.js")
    for forbidden in ("33067", "33839", "41139", "1164", "662", "504", "316"):
        assert forbidden not in script
