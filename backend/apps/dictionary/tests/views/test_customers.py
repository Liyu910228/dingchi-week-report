from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from django.urls import reverse

from apps.dictionary.models import DictionaryItem


def _body(payload: dict) -> bytes:
    return json.dumps(payload).encode("utf-8")


@pytest.mark.django_db
@pytest.mark.parametrize("method,url", [
    ("get", "/api/v1/dictionaries/customers/"),
    ("post", "/api/v1/dictionaries/customers/new/"),
    ("patch", "/api/v1/dictionaries/customers/1/"),
    ("delete", "/api/v1/dictionaries/customers/1/"),
])
def test_customer_endpoints_require_login(client, method, url) -> None:
    response = getattr(client, method)(url)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_FAILED"


@pytest.mark.django_db
@pytest.mark.parametrize("payload", [
    {"dict_code": "C_001", "dict_name": "客户"},
    {"dict_code": "C.001", "dict_name": "客户"},
    {"dict_code": "C-001", "dict_name": "客户"},
    {"dict_code": "A" * 65, "dict_name": "客户"},
    {"dict_code": "C001", "dict_name": "客" * 129},
])
def test_customer_create_validation_returns_400(client, payload) -> None:
    with patch("apps.dictionary.views.require_user", return_value=(object(), "system_admin")):
        response = client.post(
            reverse("dictionary:customer-create"),
            data=_body(payload),
            content_type="application/json",
        )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"
    assert not DictionaryItem.objects.filter(dict_type="customer").exists()


@pytest.mark.django_db
def test_customer_list_requires_system_admin(client) -> None:
    with patch("apps.dictionary.views.require_user", return_value=(object(), "president")):
        response = client.get(reverse("dictionary:customers"))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.django_db
def test_customer_list_returns_persisted_items(client) -> None:
    DictionaryItem.objects.create(
        dict_type="customer", dict_code="C001", dict_name="客户一", sort_order=20
    )
    DictionaryItem.objects.create(
        dict_type="customer", dict_code="C002", dict_name="客户二", sort_order=10
    )
    DictionaryItem.objects.create(
        dict_type="role_scope", dict_code="self", dict_name="本人"
    )

    with patch("apps.dictionary.views.require_user", return_value=(object(), "system_admin")):
        response = client.get(reverse("dictionary:customers"))

    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert [item["dict_code"] for item in items] == ["C002", "C001"]
    assert all(item["dict_type"] == "customer" for item in items)


@pytest.mark.django_db
def test_customer_create_persists_and_returns_201(client) -> None:
    with patch("apps.dictionary.views.require_user", return_value=(object(), "system_admin")):
        response = client.post(
            reverse("dictionary:customer-create"),
            data=_body({"dict_code": "C001", "dict_name": "客户一", "sort_order": 5}),
            content_type="application/json",
        )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["dict_code"] == "C001"
    assert payload["dict_name"] == "客户一"
    assert payload["status"] == "active"
    assert DictionaryItem.objects.filter(dict_type="customer", dict_code="C001").exists()


@pytest.mark.django_db
def test_customer_create_rejects_invalid_payload(client) -> None:
    with patch("apps.dictionary.views.require_user", return_value=(object(), "system_admin")):
        response = client.post(
            reverse("dictionary:customer-create"),
            data=_body({"dict_code": "-bad", "dict_name": "客户"}),
            content_type="application/json",
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.django_db
def test_customer_create_rejects_invalid_utf8_as_client_error(client) -> None:
    with patch("apps.dictionary.views.require_user", return_value=(object(), "system_admin")):
        response = client.post(
            reverse("dictionary:customer-create"),
            data=b"\xff",
            content_type="application/json",
        )
    assert response.status_code == 400
    assert response.json()["error"]["message"] == "请求体必须使用 UTF-8 编码。"


@pytest.mark.django_db
def test_customer_create_rejects_duplicate_code(client) -> None:
    DictionaryItem.objects.create(
        dict_type="customer", dict_code="C001", dict_name="客户一"
    )
    with patch("apps.dictionary.views.require_user", return_value=(object(), "system_admin")):
        response = client.post(
            reverse("dictionary:customer-create"),
            data=_body({"dict_code": "C001", "dict_name": "客户二"}),
            content_type="application/json",
        )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CUSTOMER_CONFLICT"


@pytest.mark.django_db
def test_customer_update_modifies_fields(client) -> None:
    item = DictionaryItem.objects.create(
        dict_type="customer", dict_code="C001", dict_name="客户一", sort_order=0
    )
    with patch("apps.dictionary.views.require_user", return_value=(object(), "system_admin")):
        response = client.patch(
            reverse("dictionary:customer-detail", args=[item.id]),
            data=_body({"dict_name": "客户一-更新", "status": "inactive"}),
            content_type="application/json",
        )

    assert response.status_code == 200
    assert response.json()["data"]["dict_name"] == "客户一-更新"
    assert response.json()["data"]["status"] == "inactive"


@pytest.mark.django_db
def test_customer_update_returns_not_found_for_unknown(client) -> None:
    with patch("apps.dictionary.views.require_user", return_value=(object(), "system_admin")):
        response = client.patch(
            reverse("dictionary:customer-detail", args=[999_999_999]),
            data=_body({"dict_name": "新名"}),
            content_type="application/json",
        )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CUSTOMER_NOT_FOUND"


@pytest.mark.django_db
def test_customer_update_returns_not_found_for_non_customer_item(client) -> None:
    item = DictionaryItem.objects.create(
        dict_type="role_scope", dict_code="self", dict_name="本人"
    )
    with patch("apps.dictionary.views.require_user", return_value=(object(), "system_admin")):
        response = client.patch(
            reverse("dictionary:customer-detail", args=[item.id]),
            data=_body({"dict_name": "新名"}),
            content_type="application/json",
        )

    assert response.status_code == 404


@pytest.mark.django_db
def test_customer_delete_marks_deleted(client) -> None:
    item = DictionaryItem.objects.create(
        dict_type="customer", dict_code="C001", dict_name="客户一"
    )
    with patch("apps.dictionary.views.require_user", return_value=(object(), "system_admin")):
        response = client.delete(reverse("dictionary:customer-detail", args=[item.id]))

    assert response.status_code == 200
    assert response.json()["data"]["deleted"] is True
    assert (
        DictionaryItem.objects.get(id=item.id).status == "deleted"
    )


@pytest.mark.django_db
def test_customer_delete_returns_not_found_for_unknown(client) -> None:
    with patch("apps.dictionary.views.require_user", return_value=(object(), "system_admin")):
        response = client.delete(reverse("dictionary:customer-detail", args=[999_999_999]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_customer_endpoints_reject_non_admin(client) -> None:
    item = DictionaryItem.objects.create(
        dict_type="customer", dict_code="C001", dict_name="客户一"
    )
    with patch(
        "apps.dictionary.views.require_user",
        return_value=(object(), "delivery_specialist"),
    ):
        post = client.post(
            reverse("dictionary:customer-create"),
            data=_body({"dict_code": "C999", "dict_name": "新客户"}),
            content_type="application/json",
        )
        patch_resp = client.patch(
            reverse("dictionary:customer-detail", args=[item.id]),
            data=_body({"dict_name": "X"}),
            content_type="application/json",
        )
        delete_resp = client.delete(reverse("dictionary:customer-detail", args=[item.id]))

    assert post.status_code == 403
    assert patch_resp.status_code == 403
    assert delete_resp.status_code == 403
