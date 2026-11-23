from .models import ApprovalRequest, ApprovalStep


def requests(business_type, business_id):
    return ApprovalRequest.objects.filter(
        business_type=business_type, business_id=business_id
    ).order_by("-created_at", "-id")


def steps(request_id):
    return ApprovalStep.objects.filter(approval_id=request_id).order_by("sort_order")


def create_request(**fields):
    return ApprovalRequest.objects.create(**fields)


def create_steps(request_id, approvers):
    return ApprovalStep.objects.bulk_create(
        [
            ApprovalStep(
                approval_id=request_id,
                approver_id=int(item["id"]),
                approver_name=item["name"],
                approver_role_code=item["role_code"],
                sort_order=index,
                status="pending" if index == 0 else "waiting",
            )
            for index, item in enumerate(approvers)
        ]
    )


def lock_request(request_id):
    return ApprovalRequest.objects.select_for_update().get(id=request_id)


def has_pending_request(business_type, business_id):
    return requests(business_type, business_id).filter(status="pending").exists()


def step_at(request_id, sort_order):
    return steps(request_id).filter(sort_order=sort_order).first()


def save_step(step):
    step.save()


def cancel_waiting_steps(request_id):
    return steps(request_id).filter(status="waiting").update(status="cancelled")


def save_request(request):
    request.save()


def participant_business_ids(user_id, business_type, pending_only=False, role_code=None):
    step_rows = ApprovalStep.objects.filter(approver_id=user_id)
    if role_code is not None:
        step_rows = step_rows.filter(
            approver_role_code__in=[role_code] if isinstance(role_code, str) else role_code
        )
    if pending_only:
        step_rows = step_rows.filter(status="pending")
    request_ids = list(step_rows.values_list("approval_id", flat=True))
    rows = ApprovalRequest.objects.filter(id__in=request_ids, business_type=business_type)
    if pending_only:
        rows = rows.filter(status="pending")
    return list(rows.values_list("business_id", flat=True))


def _assigned_requests(user_id, business_type, business_ids, status, pending_only, role_code=None):
    # 只有已轮到或已处理的节点进入审批列表；未激活、上级驳回后取消的节点不可见。
    assigned = ApprovalStep.objects.filter(
        approver_id=user_id, status__in=["pending", "approved", "rejected"]
    )
    if role_code is not None:
        assigned = assigned.filter(
            approver_role_code__in=[role_code] if isinstance(role_code, str) else role_code
        )
    if pending_only:
        assigned = assigned.filter(status="pending")
    ids = list(assigned.values_list("approval_id", flat=True))
    types = [business_type] if isinstance(business_type, str) else list(business_type)
    rows = ApprovalRequest.objects.filter(
        id__in=ids, business_type__in=types, business_id__in=business_ids
    ).order_by("-created_at", "-id")
    if status:
        rows = rows.filter(status=status)
    if pending_only:
        rows = rows.filter(status="pending")
    return rows


def assigned_requests(
    user_id, business_type, business_ids, status, pending_only, page, size, role_code=None
):
    rows = _assigned_requests(
        user_id, business_type, business_ids, status, pending_only, role_code
    )
    return rows.count(), list(rows[(page - 1) * size : page * size])


def assigned_snapshots(user_id, business_type, business_ids, role_codes):
    return _assigned_requests(
        user_id, business_type, business_ids, "", False, role_codes
    ).values_list("business_id", "snapshot_json")


def pending_requests(user_id, role_code=None):
    steps = ApprovalStep.objects.filter(approver_id=user_id, status="pending")
    if role_code is not None:
        steps = steps.filter(
            approver_role_code__in=[role_code] if isinstance(role_code, str) else role_code
        )
    ids = steps.values_list("approval_id", flat=True)
    return list(
        ApprovalRequest.objects.filter(
            id__in=list(ids),
            status="pending",
            business_type__in=[
                "monthly_plan",
                "monthly_plan_change",
                "monthly_submission",
                "monthly_submission_change",
            ],
        )
    )


def find_request(request_id):
    return ApprovalRequest.objects.filter(id=request_id).first()
