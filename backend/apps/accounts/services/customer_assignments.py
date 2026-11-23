"""职位和用户客户配置；客户必须来自系统启用客户字典。"""

from django.db import transaction

from apps.dictionary.public import list_active_dictionary_items

from .. import customer_assignment_dao as dao


def customer_options():
    return {int(item["id"]): item for item in list_active_dictionary_items("customer")}


def normalize_ids(value):
    if not isinstance(value, list):
        raise ValueError("客户必须为ID数组。")
    try:
        ids = [int(str(item)) for item in value]
    except (TypeError, ValueError) as exc:
        raise ValueError("客户ID格式无效。") from exc
    if len(ids) != len(set(ids)) or len(ids) > 1000:
        raise ValueError("客户重复或超过允许数量。")
    if set(ids) - customer_options().keys():
        raise ValueError("存在不存在或已停用的客户。")
    return ids


@transaction.atomic
def set_role_customers(role_id, values):
    dao.replace_role_customers(role_id, normalize_ids(values))


def user_assignments(user_id):
    roles = {role.id: role.role_code for role in dao.assigned_roles(user_id)}
    result = {code: [] for code in roles.values()}
    for row in dao.user_customer_rows(user_id):
        if row.role_id in roles:
            result[roles[row.role_id]].append(str(row.customer_id))
    return result


@transaction.atomic
def set_user_customers(user_id, value=None):
    roles = {role.role_code: role for role in dao.assigned_roles(user_id)}
    source = user_assignments(user_id) if value is None else value
    if not isinstance(source, dict) or set(source) - roles.keys():
        raise ValueError("客户配置包含未分配的职位。")
    assignments = {}
    for code, role in roles.items():
        ids = normalize_ids(source.get(code, []))
        if set(ids) - set(dao.role_customer_ids(role.id)):
            raise ValueError("用户客户必须在对应职位负责的客户范围内。")
        assignments[role.id] = ids
    dao.replace_user_customers(user_id, assignments)
