from .models import Role, RoleCustomer, UserRole, UserRoleCustomer


def role_customer_ids(role_id):
    return list(
        RoleCustomer.objects.filter(role_id=role_id)
        .order_by("sort_order", "id")
        .values_list("customer_id", flat=True)
    )


def user_customer_rows(user_id):
    return list(UserRoleCustomer.objects.filter(user_id=user_id).order_by("sort_order", "id"))


def replace_role_customers(role_id, ids):
    RoleCustomer.objects.filter(role_id=role_id).delete()
    RoleCustomer.objects.bulk_create(
        [
            RoleCustomer(role_id=role_id, customer_id=value, sort_order=index)
            for index, value in enumerate(ids)
        ]
    )
    UserRoleCustomer.objects.filter(role_id=role_id).exclude(customer_id__in=ids).delete()


def replace_user_customers(user_id, assignments):
    UserRoleCustomer.objects.filter(user_id=user_id).delete()
    UserRoleCustomer.objects.bulk_create(
        [
            UserRoleCustomer(user_id=user_id, role_id=role_id, customer_id=value, sort_order=index)
            for role_id, ids in assignments.items()
            for index, value in enumerate(ids)
        ]
    )


def assigned_roles(user_id):
    ids = list(
        UserRole.objects.filter(user_id=user_id, status="active").values_list("role_id", flat=True)
    )
    return list(Role.objects.filter(id__in=ids, status="active").order_by("sort_order", "id"))
