from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def test_strategy_flow_decorations_are_idempotent_under_mutation_updates() -> None:
    js = (WEB / "product-ui.js").read_text(encoding="utf-8")

    assert "if(marker.className!==markerClass)marker.className=markerClass" in js
    assert "if(marker.textContent!==result.label)marker.textContent=result.label" in js
    # classList.toggle(name, force) is itself idempotent and avoids duplicate class work.
    assert "node.classList.toggle('done',done)" in js
    assert "if(guide.dataset.nutevGuideSignature===signature)return" in js
    assert "guide.dataset.nutevGuideSignature=signature" in js
    assert "if(note.textContent!==copy)note.textContent=copy" in js


def test_product_ui_observer_updates_only_added_subtrees_and_targeted_surfaces() -> None:
    js = (WEB / "product-ui.js").read_text(encoding="utf-8")

    assert "const observer=new MutationObserver" in js
    assert "for(const node of mutation.addedNodes)" in js
    assert "translateInternalEnums(node)" in js
    assert "markStaticKpis(element)" in js
    assert "if(summaryChanged)explainResultCap()" in js
    assert "if(strategyChanged){ensureStrategyFlowGuide();decorateStrategyFlow()}" in js
    assert "if(changed)applyProductUi(document)" not in js
    assert "observer.observe(document.documentElement,{childList:true,subtree:true})" in js
