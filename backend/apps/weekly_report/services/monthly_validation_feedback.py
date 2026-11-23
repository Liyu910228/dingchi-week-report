"""月度填写错误的用户可读位置与类别，不暴露内部字段或堆栈。"""

from collections.abc import Mapping


def scope_label(template_code=""):
    if template_code == "human_resources_v1":
        return "模块"
    if template_code in {"recruitment_v1", "ito_sales_v1"}:
        return "维度"
    return "客户" if template_code else "客户/维度/模块"


def task_location(task, index, template_code=""):
    location = f"月度计划第{index}条"
    if not isinstance(task, Mapping):
        return location
    scope = task.get("scope_name") or task.get("customer_name") or task.get("dimension")
    if isinstance(scope, str) and scope.strip():
        location += f"，{scope_label(template_code)}「{' '.join(scope.split())[:60]}」"
    title = task.get("work_task")
    if isinstance(title, str) and title.strip():
        location += f"，工作任务「{' '.join(title.split())[:40]}」"
    return location


def validation_feedback(message):
    if "系统错误" in message or "填写内容校验不通过" in message:
        return message
    return f"填写内容校验不通过：{message}"
