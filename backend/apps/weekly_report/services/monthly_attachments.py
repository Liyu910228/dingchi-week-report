"""月度计划附件归属校验与绑定；移除关联不破坏审批历史文件。"""

from django.core.files.storage import default_storage

from .. import monthly_attachment_dao as dao
from .monthly_attachment_metadata import attachment_metadata
from .monthly_validation_feedback import task_location


def descriptor(row, description):
    return {
        "id": str(row.id),
        "file_name": row.file_name,
        "mime_type": row.mime_type,
        "file_size": row.file_size,
        "file_url": row.file_url,
        "description": description,
    }


def prepare_tasks(value, user_id, plan_id, previous=()):
    if not isinstance(value, list) or any(not isinstance(task, dict) for task in value):
        raise ValueError("月度计划必须为任务数组。")
    old = {str(task.get("id")): task.get("attachments", []) for task in previous}
    tasks = [
        {
            **task,
            "attachments": attachment_metadata(
                {"attachments": task.get("attachments", old.get(str(task.get("id")), []))}
            ),
        }
        for task in value
    ]
    ids = {item["id"] for task in tasks for item in task["attachments"]}
    files = dao.locked_files(ids)
    for index, task in enumerate(tasks, 1):
        canonical = []
        for item in task["attachments"]:
            row = files.get(item["id"])
            if not row or not permitted(row, user_id, plan_id):
                raise PermissionError(
                    f"{task_location(task, index)}：相关文档附件校验不通过："
                    "附件不存在或不属于本人当前月度计划，请重新上传。"
                )
            if not row.storage_key or not default_storage.exists(row.storage_key):
                raise ValueError(
                    f"{task_location(task, index)}：相关文档附件校验不通过："
                    "附件文件不存在，请重新上传。"
                )
            canonical.append(descriptor(row, item["description"]))
        task["attachments"] = canonical
    if plan_id is not None:
        dao.bind_pending(ids, plan_id)
    return tasks


def permitted(row, user_id, plan_id):
    return (row.attachment_type == "weekly_report_pending" and row.relation_id == user_id) or (
        row.attachment_type == "monthly_plan" and row.relation_id == plan_id
    )
