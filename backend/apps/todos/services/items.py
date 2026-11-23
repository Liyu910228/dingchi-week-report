import json

from django.db import transaction

from apps.accounts.public import assigned_role_codes

from .. import dao


@transaction.atomic
def publish(*, recipient_id, role_code, source, dedupe_key, title, target):
    if (
        not role_code
        or len(role_code) > 64
        or not source
        or len(source) > 64
        or not dedupe_key
        or len(dedupe_key) > 192
        or not title
        or len(title) > 255
    ):
        raise ValueError("待办字段长度无效。")
    return dao.ensure_item(
        recipient_id,
        role_code,
        dedupe_key,
        source=source,
        title=title,
        target_json=json.dumps(target, ensure_ascii=False),
    )


@transaction.atomic
def complete(*, recipient_id, role_code, dedupe_key):
    return dao.complete_key(recipient_id, role_code, dedupe_key)


def serialize(item):
    return {
        "id": str(item.id),
        "role_code": item.role_code,
        "source": item.source,
        "title": item.title,
        "target": json.loads(item.target_json),
        "status": item.status,
        "read_at": item.read_at.isoformat() if item.read_at else None,
        "created_at": item.created_at.isoformat(),
        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
    }


def list_items(user_id, role_code, page=1):
    if page < 1:
        raise ValueError("页码必须大于0。")
    total, rows = dao.paginated_items(user_id, role_code, page)
    return {
        "role_code": role_code,
        "items": [serialize(row) for row in rows],
        "total": total,
        "unread_count": dao.unread_count(user_id, role_code),
        "page": page,
        "page_size": 10,
        "total_pages": (total + 9) // 10,
    }


@transaction.atomic
def mark_read(user_id, role_code, item_id):
    return serialize(dao.mark_read(user_id, assigned_role_codes(user_id), item_id))


@transaction.atomic
def reconcile(user_id, role_code, source, entries):
    for entry in entries:
        publish(recipient_id=user_id, source=source, **{**entry, "role_code": role_code})
    dao.complete_stale(user_id, role_code, source, [entry["dedupe_key"] for entry in entries])
