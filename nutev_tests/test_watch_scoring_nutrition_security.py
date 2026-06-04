from __future__ import annotations

from nutev.global_watch.watch_scoring import score_watch_item


def test_nutrition_security_access_signals_improve_watch_priority() -> None:
    prioritized = score_watch_item(
        {
            "title": "Nutrition security screening and food pharmacy referral for cardiometabolic care",
            "abstract": "A social prescribing program connects patients with food pantry referral and medically tailored food referral workflows.",
        }
    )
    generic = score_watch_item({"title": "Cardiometabolic care note"})

    assert prioritized > generic
