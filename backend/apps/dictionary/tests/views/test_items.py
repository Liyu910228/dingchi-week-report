from __future__ import annotations

from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.dictionary.models import DictionaryItem


@pytest.mark.django_db
def test_dictionary_items_returns_active_values_in_order(client) -> None:
    DictionaryItem.objects.create(
        dict_type="role_scope", dict_code="team", dict_name="本人及下属团队", sort_order=20
    )
    DictionaryItem.objects.create(
        dict_type="role_scope", dict_code="self", dict_name="仅本人数据", sort_order=10
    )
    DictionaryItem.objects.create(
        dict_type="role_scope",
        dict_code="hidden",
        dict_name="停用项",
        status="inactive",
        sort_order=1,
    )

    with patch("apps.dictionary.views.require_user", return_value=(object(), "system_admin")):
        response = client.get(reverse("dictionary:items", args=["role_scope"]))

    assert response.status_code == 200
    assert response.json()["data"]["items"] == [
        {
            "id": str(DictionaryItem.objects.get(dict_code="self").id),
            "dict_type": "role_scope",
            "dict_code": "self",
            "dict_name": "仅本人数据",
            "dict_value": "",
            "description": "",
            "status": "active",
            "sort_order": 10,
        },
        {
            "id": str(DictionaryItem.objects.get(dict_code="team").id),
            "dict_type": "role_scope",
            "dict_code": "team",
            "dict_name": "本人及下属团队",
            "dict_value": "",
            "description": "",
            "status": "active",
            "sort_order": 20,
        },
    ]


@pytest.mark.django_db
def test_dictionary_items_requires_authentication(client) -> None:
    with patch(
        "apps.dictionary.views.require_user",
        side_effect=ValueError("请先登录后再访问该资源。"),
    ) as require:
        require.side_effect.code = "AUTHENTICATION_FAILED"
        response = client.get(reverse("dictionary:items", args=["role_scope"]))

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_FAILED"


@pytest.mark.django_db
def test_dictionary_items_rejects_invalid_type(client) -> None:
    with patch("apps.dictionary.views.require_user", return_value=(object(), "system_admin")):
        response = client.get(reverse("dictionary:items", args=["RoleScope"]))

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_DICTIONARY_TYPE"
