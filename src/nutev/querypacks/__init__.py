from __future__ import annotations

from nutev.querypacks import builders as _builders


BEHAVIOR_CHANGE_MODEL_TERMS = [
    "behavior change technique",
    "behavior change techniques",
    "behaviour change technique",
    "behaviour change techniques",
    "behavior change wheel",
    "behaviour change wheel",
    "behavior change intervention",
    "behaviour change intervention",
    "capability opportunity motivation behavior",
    "capability opportunity motivation behaviour",
    "com-b",
    "com b",
    "intervention mapping",
    "implementation mapping",
    "self-management support",
]


def _extend_once(target: list[str], terms: list[str]) -> None:
    seen = {item.lower() for item in target}
    for term in terms:
        key = term.lower()
        if key in seen:
            continue
        target.append(term)
        seen.add(key)


def _install_behavior_change_model_terms() -> None:
    for workstream in ("busca2b", "artigo3_framework"):
        enhancements = _builders.WORKSTREAM_QUERY_ENHANCEMENTS.setdefault(workstream, {})
        _extend_once(enhancements.setdefault("focus_terms", []), BEHAVIOR_CHANGE_MODEL_TERMS)
        _extend_once(enhancements.setdefault("web_hints", []), BEHAVIOR_CHANGE_MODEL_TERMS)


_install_behavior_change_model_terms()


__all__ = ["BEHAVIOR_CHANGE_MODEL_TERMS"]
