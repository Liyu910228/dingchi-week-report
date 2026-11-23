import json
from calendar import monthrange

from django.db import transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.utils import timezone

from .models import TodoItem


def ensure_item(recipient_id, role_code, dedupe_key, **fields):
    item, created = TodoItem.objects.get_or_create(
        recipient_id=recipient_id, role_code=role_code, dedupe_key=dedupe_key, defaults=fields
    )
    if created:
        return item
    changed = []
    if item.title != fields["title"]:
        item.title = fields["title"]
        changed.append("title")
    if item.status == "completed":
        item.status, item.read_at, item.completed_at = "pending", None, None
        changed.extend(["status", "read_at", "completed_at"])
    if changed:
        item.save(update_fields=[*changed, "updated_at"])
    return item


def complete_key(recipient_id, role_code, dedupe_key):
    return TodoItem.objects.filter(
        recipient_id=recipient_id, role_code=role_code, dedupe_key=dedupe_key, status="pending"
    ).update(status="completed", completed_at=timezone.now(), updated_at=timezone.now())


def complete_stale(recipient_id, role_code, source, active_keys):
    return (
        TodoItem.objects.filter(
            recipient_id=recipient_id, role_code=role_code, source=source, status="pending"
        )
        .exclude(dedupe_key__in=active_keys)
        .update(status="completed", completed_at=timezone.now(), updated_at=timezone.now())
    )


def read_history_cutoff():
    now = timezone.now()
    month_index = now.year * 12 + now.month - 1 - 3
    year, month = divmod(month_index, 12)
    month += 1
    return now.replace(year=year, month=month, day=min(now.day, monthrange(year, month)[1]))


def paginated_items(recipient_id, role_code, page):
    rows = (
        TodoItem.objects.filter(
            recipient_id=recipient_id,
            role_code__in=([role_code] if isinstance(role_code, str) else list(role_code)) + [""],
            status="pending",
        )
        .filter(Q(read_at__isnull=True) | Q(created_at__gte=read_history_cutoff()))
        .annotate(
            read_priority=Case(
                When(read_at__isnull=True, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .order_by("read_priority", "-created_at", "-id")
    )
    return rows.count(), list(rows[(page - 1) * 10 : page * 10])


def unread_count(recipient_id, role_code):
    return TodoItem.objects.filter(
        recipient_id=recipient_id,
        role_code__in=([role_code] if isinstance(role_code, str) else list(role_code)) + [""],
        status="pending",
        read_at__isnull=True,
    ).count()


def mark_read(recipient_id, role_code, item_id):
    rows = TodoItem.objects.filter(
        id=item_id,
        recipient_id=recipient_id,
        role_code__in=([role_code] if isinstance(role_code, str) else list(role_code)) + [""],
    )
    if not rows.exists():
        raise LookupError("待办事项不存在。")
    rows.filter(read_at__isnull=True).update(read_at=timezone.now(), updated_at=timezone.now())
    return rows.get()


@transaction.atomic
def reconcile_weekly(recipient_id, entries):
    """周报提醒按人员+周期归一，兼容旧职位待办并保留已读状态。"""
    rows = list(
        TodoItem.objects.select_for_update()
        .filter(recipient_id=recipient_id, source="weekly_report")
        .order_by("created_at", "id")
    )
    keep_ids = []
    for entry in entries:
        start = entry["target"]["period_start"]
        key = f"weekly:{start}"
        matching = [row for row in rows if row.dedupe_key.endswith(f":{start}")]
        canonical = next(
            (row for row in matching if row.role_code == "" and row.dedupe_key == key), None
        )
        keeper = canonical or next((row for row in matching if row.read_at), None)
        keeper = keeper or next(iter(matching), None)
        if keeper is None:
            keeper = ensure_item(
                recipient_id,
                "",
                key,
                source="weekly_report",
                title=entry["title"],
                target_json=json.dumps(entry["target"]),
            )
        else:
            read_at = next((row.read_at for row in matching if row.read_at), None)
            if keeper.status == "completed":
                read_at = None
            keeper.role_code, keeper.dedupe_key = "", key
            keeper.title = entry["title"]
            keeper.target_json = json.dumps(entry["target"])
            keeper.status, keeper.completed_at, keeper.read_at = "pending", None, read_at
            keeper.save(
                update_fields=[
                    "role_code",
                    "dedupe_key",
                    "title",
                    "target_json",
                    "status",
                    "completed_at",
                    "read_at",
                    "updated_at",
                ]
            )
        keep_ids.append(keeper.id)
    TodoItem.objects.filter(
        recipient_id=recipient_id, source="weekly_report", status="pending"
    ).exclude(id__in=keep_ids).update(
        status="completed", completed_at=timezone.now(), updated_at=timezone.now()
    )
