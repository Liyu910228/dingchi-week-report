"""手工升级环境回填旧任务正文，保留原主键和时间。"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from apps.weekly_report.models import WeeklyReportItem, WeeklyTaskText


class Command(BaseCommand):
    help = "回填任务共享长文本；默认只预览，--apply 执行；可重复执行。"

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        rows = WeeklyReportItem.objects.filter(
            Q(task_text_id__isnull=True) | Q(work_content_text_id__isnull=True)
        )
        self.stdout.write(f"待回填任务：{rows.count()}")
        if not options["apply"]:
            return
        for report_id in rows.values_list("report_id", flat=True).distinct():
            with transaction.atomic():
                for item in WeeklyReportItem.objects.select_for_update().filter(
                    report_id=report_id
                ):
                    changes = {}
                    for kind, field, ref in (
                        ("task", "task_name_snapshot", "task_text_id"),
                        ("work", "work_content", "work_content_text_id"),
                    ):
                        if getattr(item, ref) is not None:
                            continue
                        text = WeeklyTaskText.objects.create(
                            report_id=report_id, content_type=kind, content=getattr(item, field)
                        )
                        changes.update({ref: text.id, field: ""})
                    if changes:
                        WeeklyReportItem.objects.filter(id=item.id).update(**changes)
        self.stdout.write(self.style.SUCCESS("回填完成；旧任务主键和时间保持不变。"))
