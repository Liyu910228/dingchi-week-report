"""显式注册人资模板及全部展示字段，不修改其他模板或职位绑定。"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.dictionary.models import DictionaryItem
from apps.weekly_report.models import ReportTemplate, ReportTemplateItem
from apps.weekly_report.template_definitions.human_resources import (
    human_resources_definition,
    human_resources_fields,
)


class Command(BaseCommand):
    help = "幂等注册人资周报模板及人资展示字段字典；不执行结构迁移。"

    @transaction.atomic
    def handle(self, *args, **options):
        template, _ = ReportTemplate.objects.update_or_create(
            template_code="human_resources_v1",
            defaults={
                "template_name": "人资周报",
                "description": "人力资源与行政工作周报",
                "status": "active",
            },
        )
        for index, (module, module_name, code, label, guidance) in enumerate(
            human_resources_definition()["tasks"]
        ):
            ReportTemplateItem.objects.update_or_create(
                template_id=template.id,
                task_code=code,
                defaults={
                    "section_code": module,
                    "section_name": module_name,
                    "label": label,
                    "guidance": guidance,
                    "sort_order": index,
                    "required": True,
                },
            )
        DictionaryItem.objects.update_or_create(
            dict_type="report_template",
            dict_code="human_resources_v1",
            defaults={
                "dict_name": "人资周报",
                "dict_value": "human_resources",
                "status": "active",
                "sort_order": 110,
            },
        )
        for field in human_resources_fields():
            DictionaryItem.objects.update_or_create(
                dict_type="weekly_report_fields_human_resources_v1",
                dict_code=field["field_code"],
                defaults={
                    "dict_name": field["label"],
                    "dict_value": "1",
                    "status": "active",
                    "sort_order": field["sort_order"] * 10,
                },
            )
        self.stdout.write(
            self.style.SUCCESS("人资模板及13个展示字段已注册；既有职位绑定保持不变。")
        )
