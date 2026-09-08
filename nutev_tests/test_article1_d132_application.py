from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import shutil
import sqlite3

import pytest

from nutev.applications.willian_doctorate_a1 import (
    D132ConfigurationError,
    D132Service,
    load_d132_config,
    load_d132_source,
)
from nutev.review import ReviewAccessDenied
from nutev.tenancy import Membership, Principal, WorkspaceRole, new_opaque_id

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "nutev" / "applications" / "willian_doctorate_a1_d132_v1.json"
SOURCE_DIR = ROOT / "evidence" / "article1_press" / "article1_press_20260906T202201Z"
MANIFEST = SOURCE_DIR / "HUMAN_REVIEW_SAMPLE_MANIFEST.json"
SAMPLE_FILES = tuple(SOURCE_DIR / f"HUMAN_REVIEW_SAMPLE_D0{index}.csv" for index in range(2, 6))


def _sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _principal(
    role: WorkspaceRole = WorkspaceRole.WORKSPACE_OWNER,
    *,
    workspace_id: str | None = None,
    user_id: str | None = None,
) -> tuple[Principal, str, str]:
    uid = user_id or new_opaque_id("user")
    wid = workspace_id or new_opaque_id("workspace")
    project_id = new_opaque_id("project")
    return (
        Principal(
            user_id=uid,
            workspace_memberships=(Membership(workspace_id=wid, user_id=uid, role=role),),
            global_roles=frozenset(),
            session_id=new_opaque_id("session"),
        ),
        wid,
        project_id,
    )


def _service(tmp_path: Path, *, repo_root: Path = ROOT, config_path: Path | None = None) -> D132Service:
    return D132Service(
        repo_root=repo_root,
        database_path=tmp_path / "platform" / "auth.sqlite3",
        config_path=config_path,
    )


def _copy_fixture_repo(tmp_path: Path, *, explicit_ids: list[str] | None = None) -> tuple[Path, Path]:
    repo = tmp_path / "fixture-repo"
    target_source = repo / "evidence" / "article1_press" / SOURCE_DIR.name
    target_source.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SOURCE_DIR, target_source)
    raw = json.loads(CONFIG.read_text(encoding="utf-8"))
    if explicit_ids is not None:
        raw["sampling"] = {
            "mode": "EXPLICIT_RECORD_IDS",
            "explicit_record_ids": explicit_ids,
        }
    config = repo / "config.json"
    config.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return repo, config


def test_canonical_manifest_exact_is_100_records_and_source_bytes_are_unchanged(tmp_path: Path) -> None:
    before = {path: _sha(path) for path in (MANIFEST, *SAMPLE_FILES)}
    config = load_d132_config(ROOT)
    source = load_d132_source(ROOT, config)

    assert config.protocol_id == "D-132"
    assert config.sampling_mode == "MANIFEST_EXACT"
    assert config.decision_options == ("Y", "N", "U")
    assert source.source_record_count == 100
    assert source.selected_record_count == 100
    assert source.source_run_sha256 == "2ffae67debc73bfb29e271ee1f46ac3332760704188f6be3f08817d63253b63d"
    counts: dict[str, int] = {}
    for row in source.selected_records:
        counts[row["delta_id"]] = counts.get(row["delta_id"], 0) + 1
    assert counts == {"D02": 25, "D03": 25, "D04": 25, "D05": 25}
    assert len({row["record_id"] for row in source.selected_records}) == 100
    assert {path: _sha(path) for path in before} == before


def test_two_guest_slots_receive_same_canonical_ids_in_different_deterministic_order(tmp_path: Path) -> None:
    service = _service(tmp_path)
    owner, workspace_id, project_id = _principal()
    state = service.create_round(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
    )
    guest_a = service.issue_guest_reviewer(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=state.round_id,
        slot="A",
        label="Professor A",
    )
    guest_b = service.issue_guest_reviewer(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=state.round_id,
        slot="B",
        label="Professor B",
    )

    payload_a = service.guest_payload(guest_a.token)
    payload_b = service.guest_payload(guest_b.token)
    ids_a = [item["payload"]["record_id"] for item in payload_a["assignments"]]
    ids_b = [item["payload"]["record_id"] for item in payload_b["assignments"]]
    canonical = {row["record_id"] for row in service.source().selected_records}

    assert payload_a["reviewer_slot"] == "A"
    assert payload_b["reviewer_slot"] == "B"
    assert len(ids_a) == len(ids_b) == 100
    assert set(ids_a) == set(ids_b) == canonical
    assert ids_a != ids_b
    assert [item["payload"]["packet_position"] for item in payload_a["assignments"]] == [
        str(index) for index in range(1, 101)
    ]

    forbidden = {
        "r1_decision",
        "rank",
        "score",
        "nutev_rank",
        "nutev_score",
        "machine_relevance",
        "other_reviewer_decision",
    }
    for payload in (payload_a, payload_b):
        for assignment in payload["assignments"]:
            assert forbidden.isdisjoint({key.casefold() for key in assignment["payload"]})

    with sqlite3.connect(service.store.database_path) as connection:
        token_rows = connection.execute(
            "SELECT token_hash FROM human_review_reviewers ORDER BY id"
        ).fetchall()
        d132_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(article1_d132_reviewer_slots)").fetchall()
        }
    assert len(token_rows) == 2
    assert all(len(str(row[0])) == 64 for row in token_rows)
    assert all(guest_a.token != row[0] and guest_b.token != row[0] for row in token_rows)
    assert "token" not in {name.casefold() for name in d132_columns}
    assert "token_hash" not in {name.casefold() for name in d132_columns}


def test_explicit_sampling_is_only_by_reviewed_ids_and_unknown_ids_fail_closed(tmp_path: Path) -> None:
    canonical = load_d132_source(ROOT, load_d132_config(ROOT))
    chosen = [canonical.selected_records[0]["record_id"], canonical.selected_records[30]["record_id"]]
    repo, config_path = _copy_fixture_repo(tmp_path, explicit_ids=chosen)
    config = load_d132_config(repo, config_path)
    source = load_d132_source(repo, config)
    assert config.sampling_mode == "EXPLICIT_RECORD_IDS"
    assert [row["record_id"] for row in source.selected_records] == chosen

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    raw["sampling"]["explicit_record_ids"] = ["DOES-NOT-EXIST"]
    config_path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(D132ConfigurationError, match="unknown D-132 explicit record_id"):
        load_d132_source(repo, load_d132_config(repo, config_path))


def test_forbidden_blinded_field_in_config_is_rejected(tmp_path: Path) -> None:
    repo, config_path = _copy_fixture_repo(tmp_path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    raw["review"]["allowed_fields"].append("nutev_score")
    config_path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(D132ConfigurationError, match="blinded fields"):
        load_d132_config(repo, config_path)


def test_one_record_fixture_preserves_y_n_u_lock_and_human_adjudication(tmp_path: Path) -> None:
    canonical = load_d132_source(ROOT, load_d132_config(ROOT))
    record_id = canonical.selected_records[0]["record_id"]
    repo, config_path = _copy_fixture_repo(tmp_path, explicit_ids=[record_id])
    service = _service(tmp_path, repo_root=repo, config_path=config_path)
    owner, workspace_id, project_id = _principal()
    state = service.create_round(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
    )
    guest_a = service.issue_guest_reviewer(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=state.round_id,
        slot="A",
        label="Reviewer A",
    )
    guest_b = service.issue_guest_reviewer(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=state.round_id,
        slot="B",
        label="Reviewer B",
    )
    assignment_a = service.guest_payload(guest_a.token)["assignments"][0]["assignment_id"]
    assignment_b = service.guest_payload(guest_b.token)["assignments"][0]["assignment_id"]

    service.save_guest_decision(
        guest_a.token,
        assignment_id=assignment_a,
        decision_value="U",
        reason="Resumo insuficiente; requer inspeção posterior.",
    )
    service.submit_guest(guest_a.token)
    with pytest.raises(ValueError, match="all reviewers"):
        service.adjudication_payload(
            owner,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
            round_id=state.round_id,
        )

    with pytest.raises(ValueError, match="decision_value"):
        service.save_guest_decision(
            guest_b.token,
            assignment_id=assignment_b,
            decision_value="MAYBE",
            reason="invalid",
        )
    service.save_guest_decision(
        guest_b.token,
        assignment_id=assignment_b,
        decision_value="N",
        reason="Não atende ao propósito da rota.",
    )
    service.submit_guest(guest_b.token)

    with pytest.raises(ValueError, match="locked"):
        service.save_guest_decision(
            guest_b.token,
            assignment_id=assignment_b,
            decision_value="Y",
            reason="tentativa posterior ao submit",
        )

    snapshot = service.adjudication_payload(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=state.round_id,
    )
    assert snapshot["conflict_count"] == 1
    assert {item["decision_value"] for item in snapshot["conflicts"][0]["judgments"]} == {"U", "N"}
    assert snapshot["unresolved_conflicts"] == 1

    snapshot = service.save_adjudication(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=state.round_id,
        item_key=record_id,
        decision_value="U",
        notes="Humano manteve U; requer etapa posterior, sem conversão automática.",
    )
    assert snapshot["resolved_conflicts"] == 1
    final = service.finalize_adjudication(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=state.round_id,
    )
    assert final["status"] == "complete"

    summary = service.summary(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=state.round_id,
    )
    assert summary["scientific_gate_effects"] == {
        "press_pass": False,
        "c4_decision": False,
        "gf10_authorized": False,
        "query_frozen": False,
        "formal_search_executed": False,
        "prisma_created": False,
    }


def test_guest_token_is_revalidated_every_call_after_revocation(tmp_path: Path) -> None:
    canonical = load_d132_source(ROOT, load_d132_config(ROOT))
    repo, config_path = _copy_fixture_repo(tmp_path, explicit_ids=[canonical.selected_records[0]["record_id"]])
    service = _service(tmp_path, repo_root=repo, config_path=config_path)
    owner, workspace_id, project_id = _principal()
    state = service.create_round(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
    )
    guest = service.issue_guest_reviewer(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=state.round_id,
        slot="A",
        label="Revocable guest",
    )
    assert service.guest_payload(guest.token)["reviewer_slot"] == "A"
    service.engine.revoke_guest_reviewer(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=state.round_id,
        reviewer_id=guest.reviewer.id,
    )
    with pytest.raises(ReviewAccessDenied, match="revoked"):
        service.guest_payload(guest.token)


def test_cross_project_round_id_fails_as_not_found(tmp_path: Path) -> None:
    service = _service(tmp_path)
    owner, workspace_id, project_id = _principal()
    state = service.create_round(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
    )
    wrong_project = new_opaque_id("project")
    with pytest.raises(FileNotFoundError):
        service.summary(
            owner,
            workspace_id=workspace_id,
            project_id=wrong_project,
            project_access_confirmed=True,
            round_id=state.round_id,
        )
