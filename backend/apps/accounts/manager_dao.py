from .models import OrganizationGroup, Role, UserAccount, UserManager


def role_scope(role_code):
    return (
        Role.objects.filter(role_code=role_code, status="active")
        .values_list("scope", flat=True)
        .first()
        or "self"
    )


def active_users(ids=None):
    rows = UserAccount.objects.filter(status="active")
    return rows.filter(id__in=ids) if ids is not None else rows


def profile_users(ids):
    return UserAccount.objects.filter(id__in=ids).only("id", "display_name", "group_id")


def group_names():
    return dict(OrganizationGroup.objects.values_list("id", "group_name"))


def ordered_manager_ids(user_id):
    ids = list(
        UserManager.objects.filter(user_id=user_id)
        .order_by("sort_order")
        .values_list("manager_id", flat=True)
    )
    if not ids:
        legacy = UserAccount.objects.filter(id=user_id).values_list("manager_id", flat=True).first()
        ids = [legacy] if legacy else []
    return ids


def manager_graph():
    graph = {}
    for user_id, manager_id in UserManager.objects.values_list("user_id", "manager_id"):
        graph.setdefault(user_id, []).append(manager_id)
    for user_id, manager_id in UserAccount.objects.values_list("id", "manager_id"):
        if user_id not in graph and manager_id:
            graph[user_id] = [manager_id]
    return graph


def replace_managers(user_id, ids):
    UserManager.objects.filter(user_id=user_id).delete()
    UserManager.objects.bulk_create(
        [
            UserManager(user_id=user_id, manager_id=value, sort_order=index)
            for index, value in enumerate(ids)
        ]
    )
    UserAccount.objects.filter(id=user_id).update(manager_id=ids[0] if ids else None)


def role_name(role_code):
    return (
        Role.objects.filter(role_code=role_code).values_list("role_name", flat=True).first()
        or role_code
    )


def role_names(codes):
    return dict(
        Role.objects.filter(role_code__in=codes)
        .order_by("-deletion_key")
        .values_list("role_code", "role_name")
    )
