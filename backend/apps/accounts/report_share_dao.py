"""用户主动共享配置；不扩大组织或审批权限。"""

from pathlib import Path

from django.db import connection

from .models import UserAccount, UserReportShare


def recipients(owner_id):
    return list(
        UserReportShare.objects.filter(owner_id=owner_id)
        .order_by("id")
        .values_list("recipient_id", flat=True)
    )


def replace(owner_id, ids):
    UserReportShare.objects.filter(owner_id=owner_id).delete()
    UserReportShare.objects.bulk_create(
        [UserReportShare(owner_id=owner_id, recipient_id=value) for value in ids]
    )


def valid_users(ids):
    return UserAccount.objects.filter(id__in=ids).exclude(status="deleted").count()


def owners(recipient_id):
    sql = (Path(__file__).parent / "sql/shared_report_owners.sql").read_text(encoding="utf-8")
    with connection.cursor() as cursor:
        cursor.execute(sql, [recipient_id])
        return [row[0] for row in cursor.fetchall()]
