"""月度计划/周报共享用户配置。"""

from django.db import transaction

from .. import report_share_dao as dao


@transaction.atomic
def set_shared_users(owner_id, value):
    if not isinstance(value, list) or len(value) > 1000:
        raise ValueError("共享用户必须为人员ID数组，最多1000人。")
    if any(
        isinstance(item, bool)
        or not isinstance(item, (str, int))
        or not str(item).isdigit()
        or int(item) <= 0
        for item in value
    ):
        raise ValueError("共享用户ID无效。")
    ids = [int(item) for item in value]
    if len(ids) != len(set(ids)) or owner_id in ids:
        raise ValueError("共享用户不能重复或包含本人。")
    if dao.valid_users(ids) != len(ids):
        raise ValueError("共享用户包含不存在或已删除的用户。")
    dao.replace(owner_id, ids)
    return ids
