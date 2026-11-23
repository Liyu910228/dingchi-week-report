import json

from django.db import transaction
from django.utils import timezone

from apps.accounts.public import approval_role_code, assigned_role_codes, user_profiles
from apps.todos.public import complete

from . import dao
from .todo_entries import entry, notify


@transaction.atomic
def start_approval(*, business_type, business_id, applicant_id, revision, snapshot, approvers):
    if dao.has_pending_request(business_type, business_id):
        raise ValueError("已有待审批记录，请勿重复提交。")
    request = dao.create_request(
        business_type=business_type,
        business_id=business_id,
        applicant_id=applicant_id,
        revision=revision,
        snapshot_json=json.dumps(snapshot, ensure_ascii=False),
    )
    if not approvers:
        request.status, request.completed_at = "approved", timezone.now()
        dao.save_request(request)
        return int(request.id)
    approvers = [
        {
            **person,
            "role_code": approval_role_code(int(person["id"]), snapshot.get("template_code", "")),
        }
        for person in approvers
    ]
    dao.create_steps(request.id, approvers)
    notify(request, int(approvers[0]["id"]))
    return int(request.id)


@transaction.atomic
def decide_approval(*, request_id, user_id, approve, role_code, reason=""):
    request = dao.lock_request(request_id)
    if request.status != "pending":
        raise ValueError("该审批记录已经处理。")
    step = dao.step_at(request.id, request.current_step)
    if (
        int(step.approver_id) != int(user_id)
        or step.status != "pending"
        or step.approver_role_code not in assigned_role_codes(user_id)
    ):
        raise PermissionError("当前审批尚未轮到你，无权操作。")
    reason = str(reason or "").strip()
    if not approve and not reason:
        raise ValueError("驳回必须填写原因。")
    if len(reason) > 2000:
        raise ValueError("审批意见不能超过2000字符。")
    step.status = "approved" if approve else "rejected"
    step.reason = reason
    step.acted_at = timezone.now()
    dao.save_step(step)
    next_step = dao.step_at(request.id, request.current_step + 1)
    if not approve:
        request.status = "rejected"
        dao.cancel_waiting_steps(request.id)
    elif next_step:
        next_step.status = "pending"
        dao.save_step(next_step)
        request.current_step += 1
    else:
        request.status = "approved"
    if request.status != "pending":
        request.completed_at = timezone.now()
    dao.save_request(request)
    complete(
        recipient_id=user_id, role_code=step.approver_role_code, dedupe_key=f"approval:{request.id}"
    )
    if request.status == "pending":
        notify(request, next_step.approver_id)
    return request.status


def approval_history(business_type, business_id, user_id, role_code=None):
    return [
        _serialize_request(request, user_id, role_code)
        for request in dao.requests(business_type, business_id)
    ]


def _serialize_request(request, user_id, role_code=None):
    codes = assigned_role_codes(user_id)
    steps = [
        {
            "approver_id": str(step.approver_id),
            "approver_name": step.approver_name,
            "approver_role_code": step.approver_role_code,
            "sort_order": step.sort_order,
            "status": step.status,
            "reason": step.reason,
            "acted_at": step.acted_at.isoformat() if step.acted_at else None,
        }
        for step in dao.steps(request.id)
    ]
    return {
        "id": str(request.id),
        "business_type": request.business_type,
        "revision": request.revision,
        "status": request.status,
        "created_at": request.created_at.isoformat(),
        "completed_at": request.completed_at.isoformat() if request.completed_at else None,
        "steps": steps,
        "snapshot": json.loads(request.snapshot_json),
        "can_approve": request.status == "pending"
        and any(
            step["status"] == "pending"
            and step["approver_id"] == str(user_id)
            and step["approver_role_code"] in codes
            for step in steps
        ),
    }


def participated_business_ids(user_id, business_type, pending_only=False, role_code=None):
    return dao.participant_business_ids(
        user_id, business_type, pending_only, assigned_role_codes(user_id)
    )


def assigned_approval_records(
    user_id,
    business_type,
    business_ids,
    *,
    role_code,
    status="",
    pending_only=False,
    page=1,
    size=10,
):
    """返回已轮到或已由本人处理的审批记录；分页前排除未激活节点，保留已处理历史。"""
    total, requests = dao.assigned_requests(
        user_id,
        business_type,
        business_ids,
        status,
        pending_only,
        page,
        size,
        assigned_role_codes(user_id),
    )
    records = []
    codes = assigned_role_codes(user_id)
    for request in requests:
        record = _serialize_request(request, user_id, role_code)
        own_step = next(
            step
            for step in record["steps"]
            if step["approver_id"] == str(user_id)
            and step["approver_role_code"] in codes
            and step["status"] in {"pending", "approved", "rejected"}
        )
        records.append(
            {
                **record,
                "business_id": str(request.business_id),
                "my_status": own_step["status"],
                "my_reason": own_step["reason"],
                "my_acted_at": own_step["acted_at"],
            }
        )
    return {"items": records, "total": total}


def assigned_submission_ids_for_position(user_id, submission_ids, position_code):
    """从本人有权查看的审批快照中查找曾包含指定职位的主单。"""
    rows = dao.assigned_snapshots(
        user_id, "monthly_submission", submission_ids, assigned_role_codes(user_id)
    )
    return {
        business_id
        for business_id, snapshot_json in rows
        if any(
            part.get("role_code") == position_code
            for part in json.loads(snapshot_json).get("parts", [])
        )
    }


def pending_todo_entries(user_id, role_code):
    requests = dao.pending_requests(user_id, role_code)
    profiles = user_profiles([request.applicant_id for request in requests])
    return [
        entry(
            request,
            role_code,
            profiles.get(int(request.applicant_id), {}).get("employee_name") or "未知提交人",
        )
        for request in requests
    ]


def pending_monthly_count(user_id, role_code):
    return len(dao.pending_requests(user_id, assigned_role_codes(user_id)))


def assigned_record(user_id, request_id, role_code):
    request = dao.find_request(request_id)
    if not request or not any(
        int(step.approver_id) == int(user_id)
        and step.approver_role_code in assigned_role_codes(user_id)
        and step.status in {"pending", "approved", "rejected"}
        for step in dao.steps(request_id)
    ):
        raise PermissionError("无权查看该审批记录。")
    return {
        **_serialize_request(request, user_id, role_code),
        "business_id": str(request.business_id),
    }
