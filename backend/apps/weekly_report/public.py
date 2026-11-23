"""供通用待办模块读取的周报提醒能力，不包含页面或协议实现。"""

from datetime import timedelta

from django.utils import timezone

from apps.accounts.public import report_roles

from . import reminder_dao


def weekly_reminder_entries(user, role_code):
    today = timezone.localdate()
    start = today - timedelta(days=today.weekday())
    result = []
    for role in report_roles(user.id):
        if role["role_code"] != role_code:
            continue
        if reminder_dao.has_report(user.id, role["role_code"], start):
            continue
        result.append(
            {
                "dedupe_key": f"weekly:{start}",
                "title": f"本周（{start} 至 {start + timedelta(days=6)}）周报提醒，请及时填写",
                "target": {
                    "kind": "weekly_report",
                    "period_start": str(start),
                },
            }
        )
    return result
