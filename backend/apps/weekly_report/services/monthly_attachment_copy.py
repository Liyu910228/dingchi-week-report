"""复制月度计划时为附件记录及文件创建独立副本。"""

from pathlib import PurePosixPath

from django.conf import settings
from django.core.files.storage import default_storage

from apps.core.services.id_generator import generate_primary_id

from .. import monthly_attachment_dao as dao
from .monthly_attachments import descriptor


def clone_tasks(tasks, source_id, target_id, stored_files):
    ids = {item["id"] for task in tasks for item in task.get("attachments", [])}
    originals = dao.locked_files(ids)
    copies, result = {}, []
    for task in tasks:
        items = []
        for item in task.get("attachments", []):
            key = item["id"]
            if key not in copies:
                source = originals.get(key)
                if (
                    not source
                    or source.attachment_type != "monthly_plan"
                    or source.relation_id != source_id
                ):
                    raise ValueError("月度计划附件不存在或归属错误，无法复制。")
                copies[key] = clone_file(source, target_id, stored_files)
            items.append(descriptor(copies[key], item.get("description", "")))
        result.append({**task, "attachments": items})
    return result


def clone_file(source, target_id, stored_files):
    if not source.storage_key or not default_storage.exists(source.storage_key):
        raise ValueError("月度计划附件文件不存在，无法复制。")
    key = generate_primary_id()
    name = PurePosixPath(source.storage_key).name
    folder = str(settings.ATTACHMENT_UPLOAD_DIR).strip("/")
    with default_storage.open(source.storage_key, "rb") as content:
        storage_key = default_storage.save(f"{folder}/monthly/{target_id}/{key}_{name}", content)
    stored_files.append(storage_key)
    return dao.create_file(
        id=key,
        attachment_type="monthly_plan",
        relation_id=target_id,
        storage_key=storage_key,
        file_url=f"{str(settings.MEDIA_URL).rstrip('/')}/{storage_key}",
        file_name=source.file_name,
        mime_type=source.mime_type,
        file_size=source.file_size,
        description=source.description,
    )
