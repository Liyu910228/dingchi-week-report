from __future__ import annotations

import pytest

from apps.accounts.models import OrganizationGroup, Role
from apps.accounts.services.organization import (
    RoleConflictError,
    RoleNotFoundError,
    create_role,
    delete_role,
    get_role_list,
)
from apps.dictionary.models import DictionaryItem


def _seed_role_dictionaries() -> None:
    OrganizationGroup.objects.get_or_create(
        group_code="operations",
        defaults={"group_name": "运维组", "is_system": True},
    )
    DictionaryItem.objects.bulk_create(
        [
            DictionaryItem(dict_type="role_scope", dict_code="self", dict_name="仅本人数据"),
            DictionaryItem(dict_type="role_scope", dict_code="team", dict_name="本人及下属团队"),
            DictionaryItem(dict_type="role_scope", dict_code="all", dict_name="全部数据"),
            DictionaryItem(
                dict_type="report_template",
                dict_code="delivery_specialist_v1",
                dict_name="交付专员周报",
            ),
        ]
    )


@pytest.mark.django_db
def test_role_list_keeps_inactive_roles_but_hides_deleted_roles() -> None:
    inactive_role = Role.objects.create(
        role_code="inactive_role",
        role_name="停用角色",
        status="inactive",
    )
    Role.objects.create(
        role_code="deleted_role",
        role_name="已删除角色",
        status="deleted",
    )

    role_ids = {str(item["id"]) for item in get_role_list()}

    assert str(inactive_role.id) in role_ids
    assert all(item["role_code"] != "deleted_role" for item in get_role_list())


@pytest.mark.django_db
def test_create_role_rejects_duplicate_code() -> None:
    _seed_role_dictionaries()
    Role.objects.create(role_code="duplicate_role", role_name="原角色")

    with pytest.raises(RoleConflictError):
        create_role(
            payload={
                "role_code": "duplicate_role",
                "role_name": "重复角色",
                "role_group_code": "operations",
                "report_template_code": "delivery_specialist_v1",
            }
        )


@pytest.mark.django_db
def test_create_role_requires_active_dictionary_codes() -> None:
    _seed_role_dictionaries()

    with pytest.raises(ValueError, match="数据范围"):
        create_role(
            payload={
                "role_code": "invalid_scope_role",
                "role_name": "非法范围角色",
                "scope": "department",
                "report_template_code": "delivery_specialist_v1",
            }
        )

    with pytest.raises(ValueError, match="周报模板"):
        create_role(
            payload={
                "role_code": "invalid_template_role",
                "role_name": "非法模板角色",
                "scope": "self",
                "report_template_code": "disabled_v1",
            }
        )


@pytest.mark.django_db
def test_delete_role_rejects_current_role_and_missing_role() -> None:
    role = Role.objects.create(role_code="president", role_name="总裁", scope="all")

    with pytest.raises(RoleConflictError):
        delete_role(role_id=int(role.id), acting_role_code="president")
    with pytest.raises(RoleNotFoundError):
        delete_role(role_id=999999, acting_role_code="system_admin")
