"""统一月度提交校验：全部职位通过后才允许进入审批。"""

from apps.accounts.public import account_role_name

from .monthly_plan_tasks import validate_report_monthly_data


def validate_monthly_parts(parts):
    errors = []
    for part in parts:
        payload = part.get("payload") or {}
        summary, tasks = payload.get("summary"), payload.get("tasks")
        missing = []
        if not isinstance(summary, str) or not summary.strip():
            missing.append("请填写月度目标")
        if not isinstance(tasks, list) or not tasks:
            missing.append("请至少填写一条月度计划")
        if not missing:
            try:
                validate_report_monthly_data(summary, tasks, part["template_code"])
            except ValueError as exc:
                missing.append(str(exc))
        if missing:
            label = account_role_name(part["role_code"])
            errors.append(f"{label}：{'；'.join(missing)}。")
    if errors:
        raise ValueError("\n".join(errors))
