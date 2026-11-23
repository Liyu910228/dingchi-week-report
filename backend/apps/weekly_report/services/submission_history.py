"""按批准时间提供主单的冻结历史。"""

from apps.approvals.public import approval_history

from .. import submission_dao as dao
from .monthly_plans.versions import approved_versions


def versions(parent, user_id, role_code):
    if parent.kind != "monthly":
        return []
    records = []
    for row in dao.part_rows(parent):
        records.extend(approved_versions(row, user_id))
    for source_id in [parent.id, *dao.merged_source_ids(parent.id)]:
        records.extend(
            {**r, "process_type": "initial"}
            for r in approval_history("monthly_submission", source_id, user_id, role_code)
            if r["status"] == "approved"
        )
        for change in dao.changes(source_id):
            records.extend(
                {**r, "process_type": "change", "change_id": str(change.id)}
                for r in approval_history(
                    "monthly_submission_change", change.id, user_id, role_code
                )
                if r["status"] == "approved"
            )
    records.sort(key=lambda r: (r.get("completed_at") or r["created_at"], int(r["id"])))
    return [{**record, "version": index + 1} for index, record in enumerate(records)][::-1]
