import json

from apps.accounts.public import account_role_name
from apps.approvals.public import approval_history, participated_business_ids

from ... import monthly_plan_change_dao as changes
from ..monthly_plan_tasks import list_monthly_plan_tasks


def live_snapshot(plan):
    return {
        "role_code": plan.role_code,
        "role_name": account_role_name(plan.role_code),
        "summary": plan.summary,
        "template_code": plan.template_code,
        "month_key": plan.month_key,
        "tasks": list_monthly_plan_tasks(
            employee_id=plan.employee_id, role_code=plan.role_code, month_key=plan.month_key
        ),
    }


def assigned_root_ids(user_id, role_code=None):
    roots = set(participated_business_ids(user_id, "monthly_plan", role_code=role_code))
    ids = participated_business_ids(user_id, "monthly_plan_change", role_code=role_code)
    roots.update(int(change.monthly_plan_id) for change in changes.changes_by_ids(ids))
    return list(roots)


def approved_versions(plan, user_id):
    records = [
        {**record, "process_type": "initial"}
        for record in approval_history("monthly_plan", plan.id, user_id)
        if record["status"] == "approved"
    ]
    for change in changes.changes_for_plan(plan.id):
        for record in approval_history("monthly_plan_change", change.id, user_id):
            if record["status"] == "approved":
                records.append(
                    {
                        **record,
                        "process_type": "change",
                        "change_id": str(change.id),
                        "snapshot": json.loads(change.published_snapshot_json)
                        if change.published_snapshot_json
                        else record["snapshot"],
                    }
                )
    records.sort(
        key=lambda record: (record["completed_at"] or record["created_at"], int(record["id"]))
    )
    return [
        {
            **record,
            "version": index + 1,
            "process_type": "initial" if index == 0 else "change",
            "role_code": record["snapshot"].get("role_code") or plan.role_code,
            "role_name": record["snapshot"].get("role_name") or account_role_name(plan.role_code),
        }
        for index, record in enumerate(records)
    ][::-1]


def change_row(change, *, include_snapshots=True):
    proposal = json.loads(change.proposed_snapshot_json)
    result = {
        "id": str(change.id),
        "plan_id": str(change.monthly_plan_id),
        "status": change.status,
        "revision": change.revision,
        "base_revision": change.base_revision,
        "summary": proposal["summary"],
        "rejection_reason": change.rejection_reason,
        "created_at": change.created_at.isoformat(),
        "updated_at": change.updated_at.isoformat(),
    }
    if include_snapshots:
        result.update(base_snapshot=json.loads(change.base_snapshot_json), snapshot=proposal)
    return result
