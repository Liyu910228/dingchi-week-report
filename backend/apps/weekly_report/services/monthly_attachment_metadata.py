"""附件元数据与月度任务版本一起保存，旧快照默认无附件。"""

from collections.abc import Mapping


def attachment_metadata(item):
    values = item.get("attachments", [])
    if not isinstance(values, list) or len(values) > 100:
        raise ValueError("每条月度任务附件必须为数组，最多100个。")
    result, seen = [], set()
    for value in values:
        if not isinstance(value, Mapping):
            raise ValueError("月度任务附件格式无效。")
        key = value.get("id")
        if not isinstance(key, str) or not key.isdigit() or len(key) > 20 or key in seen:
            raise ValueError("月度任务附件ID无效或重复。")
        seen.add(key)
        data = {"id": key}
        for field, limit in [
            ("file_name", 255),
            ("mime_type", 128),
            ("file_url", 10000),
            ("description", 500),
        ]:
            text = value.get(field, "")
            if not isinstance(text, str) or len(text) > limit:
                raise ValueError("月度任务附件名称或说明格式无效。")
            data[field] = text
        size = value.get("file_size", 0)
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ValueError("月度任务附件大小无效。")
        data["file_size"] = size
        result.append(data)
    return result
