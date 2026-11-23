"""提交时统一校验业务必填项，草稿不执行这些非空检查。"""

from apps.accounts.public import account_role_name, reporting_positions
from apps.weekly_report.models import WeeklyReportDailyTask, WeeklyReportMetric


def submission_errors(report, items, fields, template):
    errors = []
    task_errors = {}
    customers = {
        str(customer["id"]): customer["name"]
        for position in reporting_positions(report.employee_id)
        if position["role_code"] == report.role_code
        for customer in position.get("customers", [])
    }
    codes = {field.get("field_code") for field in fields}
    labels = {field.get("field_code"): field.get("label") for field in fields}
    required = [
        ("task_name_snapshot", labels.get("task_name") or "工作任务"),
        ("work_content", "主要工作内容"),
        ("output_description", "输出成果"),
        ("planned_completion_date", "计划完成时间"),
    ]
    if "customer_name" in codes:
        required.append(("customer_name_snapshot", "客户"))
    if "dimension" in codes:
        required.append(("section_code", labels.get("dimension") or "维度"))
    if not items:
        errors.append("本周工作至少需要一条任务。")
    for index, item in enumerate(items, 1):
        first_error = len(errors)
        for key, label in required:
            if not str(item.get(key) or "").strip():
                errors.append(f"第{index}行{label}不能为空。")
        if item.get("task_source") == "template" and any(
            not value.strip() for value in item.get("task_values", [])
        ):
            errors.append(f"第{index}行工作任务的模板占位值尚未填写完整。")
        if item.get("dimension_source") == "template" and any(
            not value.strip() for value in item.get("dimension_values", [])
        ):
            label = labels.get("dimension") or "维度"
            errors.append(f"第{index}行{label}的模板占位值尚未填写完整。")
        if item.get("customer_source") == "template" and any(
            not value.strip() for value in item.get("customer_values", [])
        ):
            errors.append(f"第{index}行客户的模板占位值尚未填写完整。")
        if (
            item.get("on_time_status") in {"late", "overdue"}
            and not str(item.get("delay_reason") or "").strip()
        ):
            errors.append(f"第{index}行进度缓慢原因说明不能为空。")
        customer = customers.get(str(item.get("customer_id"))) or str(
            item.get("customer_name_snapshot") or ""
        ).strip()
        dimension = str(item.get("section_code") or "").strip()
        location = f"「{customer}」" if customer else (
            f"「{dimension}」" if dimension else "本周工作任务"
        )
        row_errors = errors[first_error:]
        del errors[first_error:]
        if row_errors:
            prefix = f"第{index}行"
            messages = [message.removeprefix(prefix).rstrip("。") for message in row_errors]
            task_errors.setdefault(location, []).append(
                f"第{index}行：" + "；".join(dict.fromkeys(messages)) + "。"
            )
    position = account_role_name(report.role_code)
    grouped_errors = [
        f"「{position}」→ {location}：\n" + "\n".join(rows)
        for location, rows in task_errors.items()
    ]
    for row in WeeklyReportDailyTask.objects.filter(report_id=report.id):
        if not row.work_content.strip():
            errors.append(f"{row.work_date}日报主要工作内容不能为空。")
    metrics = {
        row.metric_code: row for row in WeeklyReportMetric.objects.filter(report_id=report.id)
    }
    for config in template.get("metrics", []):
        row = metrics.get(config["task_code"])
        if config.get("required") and (
            row is None or (row.actual_value_decimal is None and not row.value_text.strip())
        ):
            errors.append(f"指标{config['label']}不能为空。")
    return grouped_errors + [f"「{position}」：{message}" for message in errors]
