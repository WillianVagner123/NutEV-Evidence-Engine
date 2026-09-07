from tools.check_runtime_http_surface import EXPECTED_PROVIDER_IDS, validate_runtime_payloads


def _providers() -> dict[str, object]:
    return {
        "providers": [
            {"id": provider, "label": provider.replace("_", " ").title()}
            for provider in EXPECTED_PROVIDER_IDS
        ]
    }


def test_live_http_payload_contract_accepts_canonical_runtime() -> None:
    failures = validate_runtime_payloads(
        health={"status": "ok"},
        version={"commit": "abc123"},
        providers=_providers(),
        expected_commit="abc123",
    )

    assert failures == []


def test_live_http_payload_contract_fails_on_wrong_build_identity() -> None:
    failures = validate_runtime_payloads(
        health={"status": "ok"},
        version={"commit": "old"},
        providers=_providers(),
        expected_commit="new",
    )

    assert any("version.commit mismatch" in item for item in failures)


def test_live_http_payload_contract_fails_on_provider_loss_or_reordering() -> None:
    payload = _providers()
    rows = list(payload["providers"])  # type: ignore[arg-type]
    rows[0], rows[1] = rows[1], rows[0]
    payload["providers"] = rows

    failures = validate_runtime_payloads(
        health={"status": "ok"},
        version={"commit": "abc123"},
        providers=payload,
        expected_commit="abc123",
    )

    assert any("provider ids/order mismatch" in item for item in failures)


def test_live_http_payload_contract_fails_on_missing_provider_label() -> None:
    payload = _providers()
    rows = list(payload["providers"])  # type: ignore[arg-type]
    rows[3] = {"id": EXPECTED_PROVIDER_IDS[3], "label": ""}
    payload["providers"] = rows

    failures = validate_runtime_payloads(
        health={"status": "ok"},
        version={"commit": "abc123"},
        providers=payload,
        expected_commit="abc123",
    )

    assert any("provider labels missing" in item for item in failures)


def test_live_http_payload_contract_fails_when_health_is_not_ok() -> None:
    failures = validate_runtime_payloads(
        health={"status": "degraded"},
        version={"commit": "abc123"},
        providers=_providers(),
        expected_commit="abc123",
    )

    assert "health.status must be 'ok'" in failures
