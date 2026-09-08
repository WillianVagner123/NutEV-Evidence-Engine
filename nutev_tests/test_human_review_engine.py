from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3

import pytest

from nutev.review import HumanReviewEngine, ReviewAccessDenied, ReviewPolicy, SQLiteHumanReviewStore
from nutev.tenancy import (
    Membership,
    MembershipStatus,
    PermissionDenied,
    Principal,
    WorkspaceRole,
    new_opaque_id,
)


def _principal(
    role: WorkspaceRole,
    *,
    workspace_id: str | None = None,
    user_id: str | None = None,
    status: MembershipStatus = MembershipStatus.ACTIVE,
) -> tuple[Principal, str, str]:
    uid = user_id or new_opaque_id("user")
    wid = workspace_id or new_opaque_id("workspace")
    project_id = new_opaque_id("project")
    membership = Membership(
        workspace_id=wid,
        user_id=uid,
        role=role,
        status=status,
    )
    return (
        Principal(
            user_id=uid,
            workspace_memberships=(membership,),
            global_roles=frozenset(),
            session_id=new_opaque_id("session"),
        ),
        wid,
        project_id,
    )


def _principal_in_workspace(user_id: str, workspace_id: str, role: WorkspaceRole) -> Principal:
    return Principal(
        user_id=user_id,
        workspace_memberships=(
            Membership(
                workspace_id=workspace_id,
                user_id=user_id,
                role=role,
            ),
        ),
        global_roles=frozenset(),
        session_id=new_opaque_id("session"),
    )


def _engine(tmp_path) -> HumanReviewEngine:
    return HumanReviewEngine(SQLiteHumanReviewStore(tmp_path / "platform" / "human_review.sqlite3"))


def _round(engine: HumanReviewEngine, owner: Principal, workspace_id: str, project_id: str):
    return engine.create_round(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        name="Independent evidence review",
        policy=ReviewPolicy(
            decision_options=("0", "1", "2"),
            reason_required=True,
            minimum_reviewers_per_item=2,
        ),
    )


def test_guest_token_is_hash_only_and_backend_field_blinding_is_fail_closed(tmp_path) -> None:
    engine = _engine(tmp_path)
    owner, workspace_id, project_id = _principal(WorkspaceRole.WORKSPACE_OWNER)
    round_row = _round(engine, owner, workspace_id, project_id)

    issued = engine.issue_guest_reviewer(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=round_row.id,
        label="Guest Professor",
    )
    assignment = engine.assign_item(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=round_row.id,
        reviewer_id=issued.reviewer.id,
        item_key="article:1",
        payload={
            "title": "Visible title",
            "abstract": "Visible abstract",
            "doi": "10.1000/example",
            "r1_decision": "include",
            "nutev_rank": 1,
            "nutev_score": 0.99,
            "machine_relevance": "high",
            "other_reviewer_decision": "exclude",
        },
        allowed_fields={"title", "abstract", "doi"},
    )

    access = engine.access_for_guest(issued.token)
    payload = engine.review_payload(access)
    assert payload["assignments"][0]["assignment_id"] == assignment.id
    assert payload["assignments"][0]["payload"] == {
        "title": "Visible title",
        "abstract": "Visible abstract",
        "doi": "10.1000/example",
    }
    rendered = repr(payload)
    for forbidden in (
        "r1_decision",
        "nutev_rank",
        "nutev_score",
        "machine_relevance",
        "other_reviewer_decision",
    ):
        assert forbidden not in rendered

    with sqlite3.connect(engine.store.database_path) as connection:
        token_row = connection.execute(
            "SELECT token_hash FROM human_review_reviewers WHERE id = ?",
            (issued.reviewer.id,),
        ).fetchone()
        raw_database = "\n".join(
            str(row)
            for row in connection.execute(
                "SELECT token_hash, label FROM human_review_reviewers"
            ).fetchall()
        )
    assert token_row is not None
    assert token_row[0] != issued.token
    assert len(str(token_row[0])) == 64
    assert issued.token not in raw_database


def test_guest_token_tamper_revoke_and_expiry_are_enforced(tmp_path) -> None:
    engine = _engine(tmp_path)
    owner, workspace_id, project_id = _principal(WorkspaceRole.WORKSPACE_OWNER)
    round_row = _round(engine, owner, workspace_id, project_id)

    issued = engine.issue_guest_reviewer(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=round_row.id,
        label="Guest A",
    )
    with pytest.raises(ReviewAccessDenied):
        engine.access_for_guest(issued.token + "tampered")

    engine.revoke_guest_reviewer(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=round_row.id,
        reviewer_id=issued.reviewer.id,
    )
    with pytest.raises(ReviewAccessDenied, match="revoked"):
        engine.access_for_guest(issued.token)

    expiring = engine.issue_guest_reviewer(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=round_row.id,
        label="Guest B",
    )
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    with sqlite3.connect(engine.store.database_path) as connection:
        connection.execute(
            "UPDATE human_review_reviewers SET token_expires_at = ? WHERE id = ?",
            (past, expiring.reviewer.id),
        )
        connection.commit()
    with pytest.raises(ReviewAccessDenied, match="expired"):
        engine.access_for_guest(expiring.token)


def test_authenticated_reviewer_is_assignment_scoped_and_submit_locks(tmp_path) -> None:
    engine = _engine(tmp_path)
    owner, workspace_id, project_id = _principal(WorkspaceRole.WORKSPACE_OWNER)
    round_row = _round(engine, owner, workspace_id, project_id)

    reviewer_a_id = new_opaque_id("user")
    reviewer_b_id = new_opaque_id("user")
    reviewer_a = _principal_in_workspace(reviewer_a_id, workspace_id, WorkspaceRole.REVIEWER)
    reviewer_b = _principal_in_workspace(reviewer_b_id, workspace_id, WorkspaceRole.REVIEWER)
    row_a = engine.add_user_reviewer(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=round_row.id,
        reviewer_user_id=reviewer_a_id,
        label="Reviewer A",
    )
    row_b = engine.add_user_reviewer(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=round_row.id,
        reviewer_user_id=reviewer_b_id,
        label="Reviewer B",
    )
    assignment_a = engine.assign_item(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=round_row.id,
        reviewer_id=row_a.id,
        item_key="article:shared",
        payload={"title": "Shared", "secret": "hidden"},
        allowed_fields={"title"},
    )
    assignment_b = engine.assign_item(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=round_row.id,
        reviewer_id=row_b.id,
        item_key="article:shared",
        payload={"title": "Shared", "secret": "hidden"},
        allowed_fields={"title"},
    )

    access_a = engine.access_for_user(
        reviewer_a,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=round_row.id,
    )
    payload_a = engine.review_payload(access_a)
    assert [item["assignment_id"] for item in payload_a["assignments"]] == [assignment_a.id]
    assert assignment_b.id not in repr(payload_a)

    with pytest.raises(FileNotFoundError):
        engine.save_decision(
            access_a,
            assignment_id=assignment_b.id,
            decision_value="1",
            reason="attempted cross-reviewer write",
        )

    engine.save_decision(
        access_a,
        assignment_id=assignment_a.id,
        decision_value="2",
        reason="eligible",
    )
    submitted = engine.submit(access_a)
    assert submitted["locked"] is True
    with pytest.raises(ValueError, match="locked"):
        engine.save_decision(
            access_a,
            assignment_id=assignment_a.id,
            decision_value="0",
            reason="should not change after submit",
        )

    # B still owns only B's assignment and is unaffected by A's lock.
    access_b = engine.access_for_user(
        reviewer_b,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=round_row.id,
    )
    assert engine.review_payload(access_b)["assignments"][0]["assignment_id"] == assignment_b.id


def test_membership_removal_blocks_new_reviewer_access_resolution(tmp_path) -> None:
    engine = _engine(tmp_path)
    owner, workspace_id, project_id = _principal(WorkspaceRole.WORKSPACE_OWNER)
    round_row = _round(engine, owner, workspace_id, project_id)
    reviewer_id = new_opaque_id("user")
    engine.add_user_reviewer(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=round_row.id,
        reviewer_user_id=reviewer_id,
        label="Removed reviewer",
    )
    removed = Principal(
        user_id=reviewer_id,
        workspace_memberships=(
            Membership(
                workspace_id=workspace_id,
                user_id=reviewer_id,
                role=WorkspaceRole.REVIEWER,
                status=MembershipStatus.REMOVED,
            ),
        ),
        global_roles=frozenset(),
        session_id=new_opaque_id("session"),
    )
    with pytest.raises(PermissionDenied, match="active_membership_required"):
        engine.access_for_user(
            removed,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
            round_id=round_row.id,
        )


def test_cross_tenant_and_cross_project_round_ids_fail_as_not_found(tmp_path) -> None:
    engine = _engine(tmp_path)
    owner_a, workspace_a, project_a = _principal(WorkspaceRole.WORKSPACE_OWNER)
    round_a = _round(engine, owner_a, workspace_a, project_a)

    owner_b, workspace_b, project_b = _principal(WorkspaceRole.WORKSPACE_OWNER)
    with pytest.raises(FileNotFoundError):
        engine.round_summary(
            owner_b,
            workspace_id=workspace_b,
            project_id=project_b,
            project_access_confirmed=True,
            round_id=round_a.id,
        )

    wrong_project = new_opaque_id("project")
    with pytest.raises(FileNotFoundError):
        engine.round_summary(
            owner_a,
            workspace_id=workspace_a,
            project_id=wrong_project,
            project_access_confirmed=True,
            round_id=round_a.id,
        )


def test_two_independent_reviews_conflict_then_human_adjudication_and_lock(tmp_path) -> None:
    engine = _engine(tmp_path)
    owner, workspace_id, project_id = _principal(WorkspaceRole.WORKSPACE_OWNER)
    round_row = _round(engine, owner, workspace_id, project_id)

    reviewers = []
    accesses = []
    assignments = []
    for index in range(2):
        user_id = new_opaque_id("user")
        principal = _principal_in_workspace(user_id, workspace_id, WorkspaceRole.REVIEWER)
        reviewer = engine.add_user_reviewer(
            owner,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
            round_id=round_row.id,
            reviewer_user_id=user_id,
            label=f"Reviewer {index + 1}",
        )
        assignment = engine.assign_item(
            owner,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
            round_id=round_row.id,
            reviewer_id=reviewer.id,
            item_key="article:conflict",
            payload={"title": "Conflict article"},
            allowed_fields={"title"},
        )
        access = engine.access_for_user(
            principal,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
            round_id=round_row.id,
        )
        reviewers.append(reviewer)
        assignments.append(assignment)
        accesses.append(access)

    engine.save_decision(
        accesses[0],
        assignment_id=assignments[0].id,
        decision_value="2",
        reason="include",
    )
    engine.submit(accesses[0])
    with pytest.raises(ValueError, match="all reviewers"):
        engine.adjudication_payload(
            owner,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
            round_id=round_row.id,
        )

    engine.save_decision(
        accesses[1],
        assignment_id=assignments[1].id,
        decision_value="0",
        reason="exclude",
    )
    engine.submit(accesses[1])

    snapshot = engine.adjudication_payload(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=round_row.id,
    )
    assert snapshot["conflict_count"] == 1
    assert snapshot["unresolved_conflicts"] == 1
    assert {item["decision_value"] for item in snapshot["conflicts"][0]["judgments"]} == {"0", "2"}

    snapshot = engine.save_adjudication(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=round_row.id,
        item_key="article:conflict",
        decision_value="1",
        notes="Human adjudication",
    )
    assert snapshot["resolved_conflicts"] == 1
    final = engine.finalize_adjudication(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=round_row.id,
    )
    assert final["status"] == "complete"
    assert final["unresolved_conflicts"] == 0

    events = engine.audit_events(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=round_row.id,
    )
    event_types = {event["event_type"] for event in events}
    assert {
        "round_created",
        "reviewer_added",
        "assignment_created",
        "decision_saved",
        "reviewer_submitted_locked",
        "conflict_adjudicated",
        "adjudication_complete",
    }.issubset(event_types)


def test_reviewer_cannot_manage_round_and_platform_admin_is_not_workspace_bypass(tmp_path) -> None:
    engine = _engine(tmp_path)
    owner, workspace_id, project_id = _principal(WorkspaceRole.WORKSPACE_OWNER)
    round_row = _round(engine, owner, workspace_id, project_id)
    reviewer_id = new_opaque_id("user")
    reviewer = _principal_in_workspace(reviewer_id, workspace_id, WorkspaceRole.REVIEWER)
    engine.add_user_reviewer(
        owner,
        workspace_id=workspace_id,
        project_id=project_id,
        project_access_confirmed=True,
        round_id=round_row.id,
        reviewer_user_id=reviewer_id,
        label="Reviewer",
    )
    with pytest.raises(PermissionDenied):
        engine.issue_guest_reviewer(
            reviewer,
            workspace_id=workspace_id,
            project_id=project_id,
            project_access_confirmed=True,
            round_id=round_row.id,
            label="Unauthorized guest",
        )
