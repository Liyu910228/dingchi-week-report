from __future__ import annotations

import pytest

from apps.dictionary.models import DictionaryItem
from apps.dictionary.services.items import (
    InvalidDictionaryTypeError,
    get_active_items,
    has_active_code,
)


@pytest.mark.django_db
def test_active_code_and_items_ignore_inactive_rows() -> None:
    DictionaryItem.objects.create(
        dict_type="report_template", dict_code="weekly_v1", dict_name="周报"
    )
    DictionaryItem.objects.create(
        dict_type="report_template",
        dict_code="old_v1",
        dict_name="旧模板",
        status="inactive",
    )

    assert has_active_code(dict_type="report_template", dict_code="weekly_v1") is True
    assert has_active_code(dict_type="report_template", dict_code="old_v1") is False
    assert [item["dict_code"] for item in get_active_items(dict_type="report_template")] == [
        "weekly_v1"
    ]


def test_dictionary_type_must_be_lower_snake_case() -> None:
    with pytest.raises(InvalidDictionaryTypeError):
        get_active_items(dict_type="ReportTemplate")
