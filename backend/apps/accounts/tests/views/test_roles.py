from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.accounts.models import OrganizationGroup, Role, UserRole
from apps.dictionary.models import DictionaryItem


def _seed_role_dictionaries() -> None:
    OrganizationGroup.objects.get_or_create(
        group_code="delivery",
        defaults={"group_name": "交付组", "is_system": True},
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
            DictionaryItem(
                dict_type="report_template", dict_code="project_v1", dict_name="项目周报"
            ),
        ]
    )


@pytest.mark.django_db
def test_patch_role_uses_unified_detail_endpoint(client) -> None:
    _seed_role_dictionaries()
    role = Role.objects.create(
        role_code="project_specialist",
        role_name="项目专员",
        scope="self",
        report_template_code="delivery_specialist_v1",
        role_group_code="delivery",
    )

    with patch(
        "apps.accounts.views.require_request_user",
        return_value=(object(), "system_admin"),
    ):
        response = client.patch(
            reverse("accounts:role-detail", args=[str(role.id)]),
            data=json.dumps(
                {
                    "role_code": role.role_code,
                    "role_name": "高级项目专员",
                    "scope": "team",
                    "description": "负责项目交付管理",
                    "report_template_code": "project_v1",
                    "role_group_code": "delivery",
                }
            ),
            content_type="application/json",
        )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["role_name"] == "高级项目专员"
    role.refresh_from_db()
    assert role.scope == "team"
    assert role.report_template_code == "project_v1"


@pytest.mark.django_db
def test_delete_role_soft_deletes_role_and_assignments(client) -> None:
    role = Role.objects.create(
        role_code="temporary_reviewer",
        role_name="临时审核人",
        scope="team",
    )
    assignment = UserRole.objects.create(user_id=101, role_id=role.id, is_default=True)

    with patch(
        "apps.accounts.views.require_request_user",
        return_value=(object(), "system_admin"),
    ):
        response = client.delete(reverse("accounts:role-detail", args=[str(role.id)]))

    assert response.status_code == 200
    assert response.json()["data"] == {"id": str(role.id), "deleted": True}
    role.refresh_from_db()
    assignment.refresh_from_db()
    assert role.status == "deleted"
    assert assignment.status == "inactive"
    assert assignment.is_default is False


@pytest.mark.django_db
def test_delete_system_admin_role_returns_conflict(client) -> None:
    role = Role.objects.create(
        role_code="system_admin",
        role_name="系统管理员",
        scope="all",
    )

    with patch(
        "apps.accounts.views.require_request_user",
        return_value=(object(), "president"),
    ):
        response = client.delete(reverse("accounts:role-detail", args=[str(role.id)]))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ROLE_CONFLICT"
    role.refresh_from_db()
    assert role.status == "active"


@pytest.mark.django_db
@pytest.mark.parametrize("fields", [
    {"report_template_code": ""},
    {"role_group_code": ""},
    {"report_template_code": "", "role_group_code": ""},
])
def test_patch_role_can_clear_template_and_group(client, fields):
    _seed_role_dictionaries()
    role = Role.objects.create(
        role_code="clearable_role", role_name="可清空职位", scope="self",
        report_template_code="delivery_specialist_v1", role_group_code="delivery",
    )
    with patch("apps.accounts.views.require_request_user", return_value=(object(), "system_admin")):
        response = client.patch(
            reverse("accounts:role-detail", args=[str(role.id)]),
            data=json.dumps(fields), content_type="application/json",
        )
    assert response.status_code == 200
    role.refresh_from_db()
    for field, value in fields.items():
        assert getattr(role, field) == value
        assert response.json()["data"][field] == value
    if "report_template_code" not in fields:
        assert role.report_template_code == "delivery_specialist_v1"
    if "role_group_code" not in fields:
        assert role.role_group_code == "delivery"
