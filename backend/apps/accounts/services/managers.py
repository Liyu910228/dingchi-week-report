from .. import manager_dao


def validate_managers(user_id, value):
    if not isinstance(value, list):
        raise ValueError("直属上级必须为人员 ID 数组。")
    try:
        ids = [int(item) for item in value]
    except (ValueError, TypeError) as exc:
        raise ValueError("直属上级 ID 无效。") from exc
    if len(ids) != len(set(ids)) or user_id in ids:
        raise ValueError("直属上级不能重复或包含本人。")
    if manager_dao.active_users(ids).count() != len(ids):
        raise ValueError("直属上级包含不存在或已停用的人员。")
    graph = manager_dao.manager_graph()
    pending, visited = list(ids), set()
    while pending:
        current = pending.pop()
        if current == user_id:
            raise ValueError("直属上级关系不能形成循环。")
        if current not in visited:
            visited.add(current)
            pending.extend(graph.get(current, []))
    return ids


def set_managers(user_id, value):
    ids = validate_managers(user_id, value)
    manager_dao.replace_managers(user_id, ids)
    return ids


def visible_ids(user, role_code):
    scope = manager_dao.role_scope(role_code)
    active = set(manager_dao.active_users().values_list("id", flat=True))
    if scope == "all":
        return list(active)
    visible = {int(user.id)}
    if scope == "team":
        graph = manager_dao.manager_graph()
        changed = True
        while changed:
            children = {
                uid
                for uid, parents in graph.items()
                if uid in active and visible.intersection(parents)
            }
            changed = not children.issubset(visible)
            visible.update(children)
    return list(visible)


def profiles(ids):
    groups = manager_dao.group_names()
    return {
        int(user.id): {
            "employee_name": user.display_name,
            "group_name": groups.get(user.group_id, "未分组"),
        }
        for user in manager_dao.profile_users(ids)
    }
