from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest
from django.test import override_settings

from apps.weekly_report import dao
from apps.weekly_report.services.reports import _serialize_row


@pytest.mark.parametrize(
    "storage_zone,expected",
    [(UTC, "2026-10-14T05:16:46+00:00"), (ZoneInfo("Asia/Shanghai"), "2026-10-14T05:16:46+08:00")],
)
@override_settings(USE_TZ=True)
def test_raw_sql_datetime_retains_storage_timezone_in_api(monkeypatch, storage_zone, expected):
    cursor = MagicMock()
    cursor.description = [("updated_at",), ("period_start",)]
    cursor.fetchall.return_value = [(datetime(2026, 10, 14, 5, 16, 46), date(2026, 10, 12))]
    manager = MagicMock()
    manager.__enter__.return_value = cursor
    monkeypatch.setattr(
        dao, "connection", SimpleNamespace(cursor=lambda: manager, timezone=storage_zone)
    )
    row = _serialize_row(dao._fetch("SELECT updated_at, period_start FROM weekly_report", [])[0])
    assert row["updated_at"] == expected
    assert row["period_start"] == "2026-10-12"
