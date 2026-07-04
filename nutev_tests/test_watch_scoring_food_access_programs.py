from __future__ import annotations

from nutev.global_watch.watch_scoring import score_watch_item


def test_food_access_program_variants_improve_watch_priority() -> None:
    prioritized = score_watch_item(
        {
            "title": "Food as medicine program with produce prescription referral",
            "abstract": "A medically tailored meals program and food pharmacy referral for cardiometabolic care.",
        }
    )
    generic = score_watch_item({"title": "Cardiometabolic care note"})

    assert prioritized > generic
