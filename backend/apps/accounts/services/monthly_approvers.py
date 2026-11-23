from django.db import transaction

from .. import manager_dao, monthly_approver_dao


@transaction.atomic
def set_monthly_approvers(user_id, value):
    if not isinstance(value, list):
        raise ValueError("月报审批人必须为按审批顺序排列的人员 ID 数组。")
    if any(not isinstance(item, (str, int)) or isinstance(item, bool) or not str(item).isdigit()
           for item in value):
        raise ValueError("月报审批人 ID 无效。")
    ids = [int(item) for item in value]
    if len(ids) != len(set(ids)) or user_id in ids:
        raise ValueError("月报审批人不能重复或包含本人。")
    if manager_dao.active_users(ids).count() != len(ids):
        raise ValueError("月报审批人包含不存在或已停用的人员。")
    monthly_approver_dao.replace(user_id, ids)
    return ids


def get_monthly_approvers(user_id):
    ids = monthly_approver_dao.ordered_ids(user_id)
    users = {int(user.id): user for user in manager_dao.active_users(ids)}
    if len(users) != len(ids):
        raise ValueError("月报审批人中存在停用人员，请联系管理员调整。")
    return [{"id": str(value), "name": users[value].display_name} for value in ids]
