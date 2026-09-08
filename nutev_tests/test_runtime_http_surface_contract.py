from tools.check_runtime_http_surface import EXPECTED_PROVIDER_IDS, validate_runtime_payloads


def _providers() -> dict[str, object]:
    return {
        "providers": [
            {"id": provider, "label": provider.replace("_", " ").title()}
            for provider in EXPECTED_PROVIDER_IDS
        ]
    }


def _pilot_auth() -> dict[str, object]:
    return {
        "mode": "pilot",
        "login_available": True,
        "principal_endpoint": "/api/auth/me",
        "context_endpoint": "/api/context",
        "cookie": {
            "http_only": True,
            "same_site": "Lax",
            "secure_in_production": True,
        },
    }


def test_live_http_payload_contract_accepts_canonical_runtime() -> None:
    failures = validate_runtime_payloads(
        health={"status": "ok"},
        version={"commit": "abc123"},
        providers=_providers(),
        expected_commit="abc123",
        auth_status=_pilot_auth(),
        expected_auth_mode="pilot",
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


def test_final_release_contract_rejects_legacy_auth_mode() -> None:
    legacy = {
        "mode": "legacy",
        "login_available": False,
        "cookie": {
            "http_only": True,
            "secure_in_production": True,
        },
    }
    failures = validate_runtime_payloads(
        health={"status": "ok"},
        version={"commit": "abc123"},
        providers=_providers(),
        expected_commit="abc123",
        auth_status=legacy,
        expected_auth_mode="pilot",
    )
    assert any("auth mode mismatch" in item for item in failures)
    assert any("login_available" in item for item in failures)


def test_final_release_contract_requires_secure_http_only_cookie_contract() -> None:
    auth = _pilot_auth()
    auth["cookie"] = {
        "http_only": False,
        "secure_in_production": False,
    }
    failures = validate_runtime_payloads(
        health={"status": "ok"},
        version={"commit": "abc123"},
        providers=_providers(),
        expected_commit="abc123",
        auth_status=auth,
        expected_auth_mode="pilot",
    )
    assert "pilot auth cookie contract is incomplete" in failures
