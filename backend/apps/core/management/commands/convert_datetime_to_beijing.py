"""只供已确认历史 DATETIME 为 UTC 的已有库，在暂停业务写入后显式运行一次。"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from apps.core.dao import time_storage as dao
from apps.core.services.time_storage import convert_existing_times


class Command(BaseCommand):
    help = "预览/转换当前库 UTC DATETIME 到北京时间；默认只预览，--apply 需要备份文件。"

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--backup")

    def handle(self, *args, **options):
        if connection.vendor != "mysql":
            raise CommandError("该命令仅用于已确认 UTC 历史数据的 MySQL 数据库。")
        if dao.was_converted():
            self.stdout.write("已完成北京时间转换，本次不重复执行。")
            return
        tables = dao.tables()
        self.stdout.write(json.dumps(dict(tables), ensure_ascii=False))
        if not options["apply"]:
            self.stdout.write(
                "仅预览，未修改数据。执行前暂停业务写入并核实所有历史 DATETIME 都是 UTC。"
            )
            return
        if not options["backup"]:
            raise CommandError("--apply 必须提供 --backup 保存原始 ID 和时间值。")
        path = Path(options["backup"])
        if path.exists():
            raise CommandError("备份文件已存在，拒绝覆盖。")
        convert_existing_times(path, tables)
        self.stdout.write(self.style.SUCCESS("已转换为北京时间；DATE 和带时区 JSON 快照未修改。"))
