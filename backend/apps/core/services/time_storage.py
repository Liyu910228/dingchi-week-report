"""历史 DATETIME 转换的显式运维事务，不在启动时运行。"""

import json

from django.db import transaction

from apps.core.dao import time_storage as dao


def convert_existing_times(path, tables):
    if not dao.acquire_lock():
        raise ValueError("另一个转换正在运行。")
    try:
        with transaction.atomic():
            if dao.was_converted():
                return
            backup, statements = {}, []
            for table, columns in tables:
                fields, rows, sql = dao.snapshot_and_shift(table, columns)
                backup[table] = {"columns": fields, "rows": rows}
                statements.append(sql)
            with path.open("x", encoding="utf-8") as output:
                json.dump(backup, output, ensure_ascii=False, default=str)
            for sql in statements:
                dao.shift(sql)
            dao.mark_converted()
    finally:
        dao.release_lock()
