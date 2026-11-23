import pytest

from apps.accounts.dao import list_users
from apps.accounts.public import approval_managers
from apps.accounts.services import auth
from apps.accounts.services.managers import set_managers
from apps.accounts.services.monthly_approvers import set_monthly_approvers
from apps.approvals.models import ApprovalStep
from apps.weekly_report.services.monthly_plans import change_write, read, write

from .test_monthly_plan_workflow import create
from .test_monthly_plan_workflow import people as people

pytestmark = pytest.mark.django_db


def test_monthly_approvers_independent_order_and_existing_flow_frozen(people):
    owner, first, second, outsider = people
    set_managers(owner.id, [])
    set_monthly_approvers(owner.id, [str(second.id), str(first.id)])
    assert [p["id"] for p in approval_managers(owner.id)] == [str(second.id), str(first.id)]
    data = create(people)
    plan_id = int(data["plan"]["id"])
    write.submit(owner, "delivery", plan_id)
    set_monthly_approvers(owner.id, [])
    with pytest.raises(PermissionError):
        write.decide(first, "manager", plan_id, {"action": "approve"})
    result = write.decide(second, "manager", plan_id, {"action": "approve"})
    assert result["plan"]["status"] == "pending"
    result = write.decide(first, "manager", plan_id, {"action": "approve"})
    assert result["plan"]["status"] == "approved"


def test_no_approvers_save_draft_submit_auto_pass_and_change_publish(people):
    owner = people[0]
    # 即使有直属领导，也不会回退到直属领导审批。
    set_monthly_approvers(owner.id, [])
    assert read.context(owner, "delivery")["can_create"]
    assert read.context(owner, "delivery")["managers"] == []
    data = create(people)
    assert data["plan"]["status"] == "draft"
    plan_id = int(data["plan"]["id"])
    approved = write.submit(owner, "delivery", plan_id)
    assert approved["plan"]["status"] == "approved"
    assert approved["approvals"][0]["steps"] == []
    assert approved["approvals"][0]["completed_at"]
    assert approved["history"][0]["snapshot"]["summary"] == "原目标"
    assert ApprovalStep.objects.count() == 0
    child = change_write.create(owner, "delivery", plan_id)
    change_id = int(child["change"]["id"])
    change_write.save(owner, "delivery", change_id, {
        "revision": 0, "summary": "自动生效新目标", "tasks": child["snapshot"]["tasks"],
    })
    assert read.detail(owner, "delivery", plan_id)["plan"]["summary"] == "原目标"
    result = change_write.submit(owner, "delivery", change_id)
    assert result["change"]["status"] == "approved"
    final = read.detail(owner, "delivery", plan_id)
    assert final["plan"]["summary"] == "自动生效新目标"
    assert len(final["history"]) == 2
    assert read.gate(owner, "delivery", "2026-10")["approved"]


def test_approver_config_patch_clear_omission_and_directory(people):
    owner, first, second, _ = people
    auth.update_user(user=owner, payload={"monthly_approver_ids": [str(second.id), str(first.id)]})
    assert auth.serialize_user(owner)["monthly_approver_ids"] == [str(second.id), str(first.id)]
    rows = list_users(keyword="owner")
    assert rows[0]["monthly_approver_ids"] == [str(second.id), str(first.id)]
    auth.update_user(user=owner, payload={"display_name": "new"})
    assert len(approval_managers(owner.id)) == 2
    auth.update_user(user=owner, payload={"monthly_approver_ids": []})
    assert approval_managers(owner.id) == []


@pytest.mark.parametrize("invalid", ["string", [True], [1.5], ["missing"], ["999999999999999999"]])
def test_invalid_approvers_rejected_without_changes(people, invalid):
    with pytest.raises(ValueError):
        set_monthly_approvers(people[0].id, invalid)
    assert len(approval_managers(people[0].id)) == 2


def test_approvers_reject_self_duplicates_inactive_and_create_roundtrip(people, monkeypatch):
    owner, first, second, _ = people
    for ids in [[owner.id], [first.id, first.id]]:
        with pytest.raises(ValueError):
            set_monthly_approvers(owner.id, ids)
    second.status = "inactive"
    second.save()
    with pytest.raises(ValueError, match="停用"):
        set_monthly_approvers(owner.id, [second.id])
    monkeypatch.setattr(auth, "decrypt_client_password", lambda value: "password-123")
    user = auth.create_user(payload={
        "username": "new-monthly", "display_name": "new", "password": "encrypted",
        "role_codes": ["delivery"], "monthly_approver_ids": [str(first.id)],
    })
    assert auth.serialize_user(user)["monthly_approver_ids"] == [str(first.id)]
    assert user.manager_id is None
