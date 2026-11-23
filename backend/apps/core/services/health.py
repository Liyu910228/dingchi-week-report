from typing import Literal

from django.core.cache import cache
from django.db import connection

DependencyStatus = Literal["ok", "unavailable"]


def check_database() -> DependencyStatus:
    try:
        connection.ensure_connection()
    except Exception:
        return "unavailable"
    return "ok"


def check_redis() -> DependencyStatus:
    marker = "dingchi-health-check"
    try:
        cache.set(marker, "ok", timeout=10)
        return "ok" if cache.get(marker) == "ok" else "unavailable"
    except Exception:
        return "unavailable"


def check_dependencies() -> dict[str, DependencyStatus]:
    return {
        "database": check_database(),
        "redis": check_redis(),
    }
