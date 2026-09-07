from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "nutev-web"


def test_strategy_flow_decorations_are_idempotent_under_global_mutation_observer() -> None:
    js = (WEB / "product-ui.js").read_text(encoding="utf-8")

    assert "if(marker.className!==markerClass)marker.className=markerClass" in js
    assert "if(marker.textContent!==result.label)marker.textContent=result.label" in js
    assert "if(node.classList.contains('done')!==done)node.classList.toggle('done',done)" in js
    assert "if(guide.dataset.nutevGuideSignature===signature)return" in js
    assert "guide.dataset.nutevGuideSignature=signature" in js
    assert "if(note.textContent!==copy)note.textContent=copy" in js


def test_product_ui_observer_only_reapplies_on_added_nodes() -> None:
    js = (WEB / "product-ui.js").read_text(encoding="utf-8")

    assert "const observer=new MutationObserver" in js
    assert "if(mutation.addedNodes.length){changed=true;break}" in js
    assert "if(changed)applyProductUi(document)" in js
    assert "observer.observe(document.documentElement,{childList:true,subtree:true})" in js
