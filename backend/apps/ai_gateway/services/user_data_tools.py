"""AI 助手的用户数据查询工具（OpenAI function calling）。

安全边界：
- 工具执行时由网关注入当前登录用户 user_id，不接受任意用户 ID / 任意 SQL；
- 全部为只读 ORM 查询，不涉及任何写操作；
- 工具返回的数据会作为上下文交给大模型生成自然语言回答。
"""

from __future__ import annotations

import json
import logging
from typing import Any, Callable

from apps.accounts.manager_dao import ordered_manager_ids
from apps.accounts.models import (
    OrganizationGroup,
    Role,
    UserAccount,
    UserMonthlyApprover,
)
from apps.accounts.report_share_dao import owners as shared_owner_ids
from apps.accounts.report_share_dao import recipients
from apps.accounts.services.auth import get_user_roles
from apps.accounts.services.managers import visible_ids
from apps.weekly_report.models import (
    MonthlyPlan,
    MonthlyPlanTask,
    WeeklyReport,
    WeeklyReportItem,
)

logger = logging.getLogger(__name__)

# 输出规模限制，避免单次工具结果撑爆上下文
MAX_PLANS = 12
MAX_TASKS_PER_PLAN = 8
MAX_SHARED_OWNERS = 20
MAX_TEAM_MEMBERS = 30
MAX_WEEKLY_REPORTS = 8
MAX_ITEMS_PER_REPORT = 8
TEXT_LIMIT = 200

TOOLS_SCHEMA: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_my_profile",
            "description": (
                "查询当前登录用户的个人信息：工号、姓名、邮箱、电话、所属部门、"
                "直属上级、拥有的角色、月报审批人、共享关系（我共享给了谁、谁共享给我）。"
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_monthly_plans",
            "description": (
                "查询当前登录用户自己填报的月度计划（月报）：月份、角色、状态、"
                "概述与任务明细。可选参数 month_key 用于限定月份，格式 YYYY-MM。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "month_key": {
                        "type": "string",
                        "description": "限定查询的月份，格式 YYYY-MM，例如 2026-11；不传则返回全部。",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_my_weekly_reports",
            "description": (
                "查询当前登录用户【本人】填报的周报：每份周报的周期、角色、状态、"
                "风险等级、概述，以及任务条目明细（任务名、工作内容、进度、完成率、"
                "状态、下一步）。当用户询问自己的周报、某月/某周的周报内容、"
                "本周工作汇报时，必须调用本工具，严禁用月度计划数据代替周报回答。"
                "可选参数 month_key 用于限定月份，格式 YYYY-MM。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "month_key": {
                        "type": "string",
                        "description": "限定查询的月份，格式 YYYY-MM，例如 2026-11；不传则返回最近若干周。",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_weekly_data",
            "description": (
                "开放式统计/分析查询：跨表统计、排名、分布、对比、趋势等"
                "（例如「各部门周报提交率」「谁的周报数量最多」「本月风险周报分布」）。"
                "通过语义层生成 SQL 并执行，返回答案、SQL 与数据行。"
                "数据权限自动限定为当前登录用户可见范围（普通员工仅本人、领导含团队、管理员全部）。"
                "查询本人/团队的周报月报明细仍优先使用专用工具；本工具适合需要自由统计分析的问题。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "完整的自然语言统计问题，含时间范围等条件。",
                    }
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_shared_monthly_reports",
            "description": (
                "查询其他用户只读共享给当前登录用户的月度计划（月报）与周报："
                "共享人及其月度计划明细。可选参数 month_key 用于限定月份，格式 YYYY-MM。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "month_key": {
                        "type": "string",
                        "description": "限定查询的月份，格式 YYYY-MM，例如 2026-11；不传则返回全部。",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_team_monthly_reports",
            "description": (
                "查询当前登录用户下属团队（含本人）所有成员的月度计划（月报）概览。"
                "仅限具备团队（team）或全局（all）数据范围角色的用户（领导）使用。"
                "可选 month_key 限定月份（YYYY-MM）；可选 member_name 指定某位下属姓名，"
                "返回该成员的月报详情（含任务明细）。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "month_key": {
                        "type": "string",
                        "description": "限定查询的月份，格式 YYYY-MM，例如 2026-11；不传则返回全部。",
                    },
                    "member_name": {
                        "type": "string",
                        "description": "下属成员姓名；传入时只返回该成员的月报详情（含任务明细）。",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_team_weekly_reports",
            "description": (
                "查询当前登录用户下属团队（含本人）所有成员的周报概览："
                "每人的周报周期、状态、风险与条目数。"
                "仅限具备团队（team）或全局（all）数据范围角色的用户（领导）使用。"
                "可选 month_key 限定月份（YYYY-MM，周报按所属月份归档）；"
                "可选 member_name 指定某位下属姓名，返回该成员的周报详情"
                "（含每份周报的任务条目：任务名、工作内容、进度、完成率、状态）。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "month_key": {
                        "type": "string",
                        "description": "限定查询的月份，格式 YYYY-MM，例如 2026-11；不传则返回最近若干周。",
                    },
                    "member_name": {
                        "type": "string",
                        "description": "下属成员姓名；传入时只返回该成员的周报详情（含任务条目明细）。",
                    },
                },
                "required": [],
            },
        },
    },
]


def _clip(text: str | None, limit: int = TEXT_LIMIT) -> str:
    if not text:
        return ""
    return text if len(text) <= limit else text[:limit] + "…"


def _display_name_map(ids: list[int]) -> dict[int, str]:
    ids = [i for i in ids if i]
    if not ids:
        return {}
    return {
        row["id"]: row["display_name"]
        for row in UserAccount.objects.filter(id__in=ids, status="active").values(
            "id", "display_name"
        )
    }


def _plan_task_rows(employee_id: int, role_code: str, month_key: str) -> list[dict[str, Any]]:
    rows = (
        MonthlyPlanTask.objects.filter(
            employee_id=employee_id, role_code=role_code, month_key=month_key
        )
        .order_by("sort_order", "id")
        .values("sort_order", "scope_name", "work_task", "work_content", "planned_date")
    )[:MAX_TASKS_PER_PLAN]
    return [
        {
            "序号": row["sort_order"],
            "任务": _clip(row["work_task"]),
            "工作内容": _clip(row["work_content"]),
            "计划日期": str(row["planned_date"] or ""),
        }
        for row in rows
    ]


def _plan_dicts(
    employee_id: int, month_key: str | None, include_tasks: bool = True
) -> list[dict[str, Any]]:
    queryset = MonthlyPlan.objects.filter(employee_id=employee_id).order_by("-month_key", "role_code")
    if month_key:
        queryset = queryset.filter(month_key=month_key)
    plans = list(queryset.values("month_key", "role_code", "status", "revision", "summary", "rejection_reason")[:MAX_PLANS])
    if not plans:
        return []

    role_name_map = {
        row["role_code"]: row["role_name"]
        for row in Role.objects.filter(
            role_code__in={p["role_code"] for p in plans}, status="active"
        ).values("role_code", "role_name")
    }
    result = []
    for plan in plans:
        if include_tasks:
            tasks = _plan_task_rows(employee_id, plan["role_code"], plan["month_key"])
            task_count = len(tasks)
            task_block: Any = tasks
        else:
            task_count = MonthlyPlanTask.objects.filter(
                employee_id=employee_id,
                role_code=plan["role_code"],
                month_key=plan["month_key"],
            ).count()
            task_block = f"共 {task_count} 项（如需明细请指定成员姓名查询）"
        result.append(
            {
                "月份": plan["month_key"],
                "角色": role_name_map.get(plan["role_code"], plan["role_code"]),
                "状态": plan["status"],
                "版本": plan["revision"],
                "概述": _clip(plan["summary"]),
                "驳回原因": _clip(plan["rejection_reason"]) if plan["rejection_reason"] else "",
                "任务数": task_count,
                "任务明细": task_block,
            }
        )
    return result


def get_my_profile(user_id: int) -> dict[str, Any]:
    user = (
        UserAccount.objects.filter(id=user_id)
        .values(
            "employee_no",
            "display_name",
            "email",
            "phone",
            "group_id",
            "status",
            "last_login_at",
            "created_at",
        )
        .first()
    )
    if not user:
        return {"error": "用户不存在或已删除。"}

    group_name = (
        OrganizationGroup.objects.filter(id=user["group_id"])
        .values_list("group_name", flat=True)
        .first()
        if user["group_id"]
        else None
    )
    manager_names = [
        _display_name_map([i]).get(i, f"用户{i}")
        for i in ordered_manager_ids(user_id)
    ]
    approver_ids = list(
        UserMonthlyApprover.objects.filter(user_id=user_id)
        .order_by("sort_order")
        .values_list("approver_id", flat=True)
    )
    approver_map = _display_name_map(approver_ids)
    shared_to_ids = recipients(user_id)
    shared_from_ids = shared_owner_ids(user_id)

    return {
        "工号": user["employee_no"],
        "姓名": user["display_name"],
        "邮箱": user["email"],
        "电话": user["phone"],
        "部门": group_name or "",
        "账号状态": user["status"],
        "最近登录": str(user["last_login_at"] or ""),
        "直属上级": manager_names,
        "角色列表": [
            {"角色编码": r.role_code, "角色名称": r.role_name, "数据范围": r.scope}
            for r in get_user_roles(user_id)
        ],
        "月报审批人": [approver_map.get(i, f"用户{i}") for i in approver_ids],
        "我共享给": _display_name_map(shared_to_ids),
        "共享给我": _display_name_map(shared_from_ids),
    }


def get_my_monthly_plans(user_id: int, month_key: str | None = None) -> dict[str, Any]:
    plans = _plan_dicts(user_id, month_key)
    if not plans:
        return {"月度计划": [], "提示": "当前用户没有匹配的月度计划记录。"}
    return {"月度计划": plans}


def get_my_weekly_reports(user_id: int, month_key: str | None = None) -> dict[str, Any]:
    reports = _weekly_report_dicts(user_id, month_key, include_items=True)
    if not reports:
        return {"周报": [], "提示": "当前用户没有匹配的周报记录。"}
    return {"周报": reports}


def query_weekly_data(user_id: int, question: str) -> dict[str, Any]:
    if not question or not question.strip():
        return {"error": "question 参数不能为空。"}
    from apps.ontology.services import ask_for_user

    return ask_for_user(user_id, question.strip())


def get_shared_monthly_reports(user_id: int, month_key: str | None = None) -> dict[str, Any]:
    owner_ids = shared_owner_ids(user_id)[:MAX_SHARED_OWNERS]
    if not owner_ids:
        return {"共享月报": [], "提示": "暂无其他用户共享月报给当前用户。"}

    owners = {
        row["id"]: row
        for row in UserAccount.objects.filter(id__in=owner_ids, status="active").values(
            "id", "employee_no", "display_name"
        )
    }
    shared = []
    for owner_id in owner_ids:
        owner = owners.get(owner_id)
        if not owner:
            continue
        plans = _plan_dicts(owner_id, month_key)
        shared.append(
            {
                "共享人": owner["display_name"],
                "工号": owner["employee_no"],
                "月度计划": plans,
            }
        )
    return {"共享月报": shared}


def _weekly_report_dicts(
    employee_id: int, month_key: str | None, include_items: bool = False
) -> list[dict[str, Any]]:
    queryset = WeeklyReport.objects.filter(employee_id=employee_id).order_by(
        "-period_start", "role_code"
    )
    if month_key:
        queryset = queryset.filter(month_key=month_key)
    reports = list(
        queryset.values(
            "id",
            "month_key",
            "role_code",
            "period_start",
            "period_end",
            "status",
            "summary",
            "risk_level",
            "risk_reason",
            "next_action",
            "support_needed",
        )[:MAX_WEEKLY_REPORTS]
    )
    if not reports:
        return []

    role_name_map = {
        row["role_code"]: row["role_name"]
        for row in Role.objects.filter(
            role_code__in={r["role_code"] for r in reports}, status="active"
        ).values("role_code", "role_name")
    }

    result = []
    for report in reports:
        report_id = report["id"]
        role_name = role_name_map.get(report["role_code"], report["role_code"])
        base = {
            "月份": report["month_key"],
            "周期": f"{report['period_start']} ~ {report['period_end']}",
            "角色": role_name,
            "状态": report["status"],
            "风险等级": report["risk_level"],
        }
        if include_items:
            items = WeeklyReportItem.objects.filter(report_id=report_id).order_by(
                "sort_order", "id"
            ).values(
                "sort_order",
                "task_name_snapshot",
                "work_content",
                "progress_percent",
                "completion_rate",
                "on_time_status",
                "next_action",
            )[:MAX_ITEMS_PER_REPORT]
            item_list = []
            for item in items:
                item_list.append(
                    {
                        "序号": item["sort_order"],
                        "任务": _clip(item["task_name_snapshot"]),
                        "工作内容": _clip(item["work_content"]),
                        "进度": str(item["progress_percent"]) if item["progress_percent"] is not None else "",
                        "完成率": str(item["completion_rate"]) if item["completion_rate"] is not None else "",
                        "状态": item["on_time_status"],
                        "下一步": _clip(item["next_action"], 100),
                    }
                )
            base.update(
                {
                    "概述": _clip(report["summary"]),
                    "风险原因": _clip(report["risk_reason"]) if report["risk_reason"] else "",
                    "下一步": _clip(report["next_action"], 100) if report["next_action"] else "",
                    "需支持事项": _clip(report["support_needed"], 100) if report["support_needed"] else "",
                    "任务条目": item_list,
                }
            )
        else:
            item_count = WeeklyReportItem.objects.filter(report_id=report_id).count()
            base["条目数"] = item_count
            base["概述"] = _clip(report["summary"], 80)
        result.append(base)
    return result


def _team_scope_role(user_id: int) -> tuple[str, str] | None:
    """返回 (scope, role_code)；具备 team/all 数据范围才可查团队，否则 None。"""
    best: tuple[str, str] | None = None
    for role in get_user_roles(user_id):
        if role.scope == "all":
            return ("all", role.role_code)
        if role.scope == "team":
            best = ("team", role.role_code)
    return best


def get_team_monthly_reports(
    user_id: int,
    month_key: str | None = None,
    member_name: str | None = None,
) -> dict[str, Any]:
    scope_info = _team_scope_role(user_id)
    if scope_info is None:
        return {
            "error": (
                "当前用户没有团队数据权限：查询下属团队月报需要"
                "「团队」或「全局」数据范围的角色（领导权限）。"
            )
        }
    scope, role_code = scope_info

    user = UserAccount.objects.filter(id=user_id).only("id").first()
    if user is None:
        return {"error": "用户不存在或已删除。"}
    member_ids = visible_ids(user, role_code)

    # 指定成员姓名：返回该成员月报详情（含任务明细）
    if member_name:
        members = UserAccount.objects.filter(
            id__in=member_ids, status="active", display_name=member_name
        ).values("id", "employee_no", "display_name")
        member = members.first()
        if member is None:
            return {
                "error": f"团队中没有名为「{member_name}」的在职成员（团队共 {len(member_ids)} 人）。"
            }
        plans = _plan_dicts(member["id"], month_key, include_tasks=True)
        return {
            "数据范围": "团队成员详情",
            "成员": member["display_name"],
            "工号": member["employee_no"],
            "月度计划": plans,
        }

    # 默认：团队全员月报概览（不含任务明细，控制数据量）
    member_ids = member_ids[:MAX_TEAM_MEMBERS]
    rows = UserAccount.objects.filter(id__in=member_ids, status="active").values(
        "id", "employee_no", "display_name", "group_id"
    ).order_by("employee_no")
    group_names = {
        row["id"]: row["group_name"]
        for row in OrganizationGroup.objects.values("id", "group_name")
    }

    members = []
    for row in rows:
        member = {
            "姓名": row["display_name"],
            "工号": row["employee_no"],
            "部门": group_names.get(row["group_id"], ""),
            "是否本人": row["id"] == user_id,
            "月度计划": _plan_dicts(row["id"], month_key, include_tasks=False),
        }
        if not member["月度计划"]:
            member["月度计划"] = f"无{month_key or ''}月度计划记录"
        members.append(member)

    return {
        "数据范围": "下属团队全员（含本人）" if scope == "team" else "全员",
        "团队人数": len(member_ids),
        "月度计划概览": members,
    }


def get_team_weekly_reports(
    user_id: int,
    month_key: str | None = None,
    member_name: str | None = None,
) -> dict[str, Any]:
    scope_info = _team_scope_role(user_id)
    if scope_info is None:
        return {
            "error": (
                "当前用户没有团队数据权限：查询下属团队周报需要"
                "「团队」或「全局」数据范围的角色（领导权限）。"
            )
        }
    scope, role_code = scope_info

    user = UserAccount.objects.filter(id=user_id).only("id").first()
    if user is None:
        return {"error": "用户不存在或已删除。"}
    member_ids = visible_ids(user, role_code)

    # 指定成员姓名：返回该成员周报详情（含任务条目明细）
    if member_name:
        member = (
            UserAccount.objects.filter(
                id__in=member_ids, status="active", display_name=member_name
            )
            .values("id", "employee_no", "display_name")
            .first()
        )
        if member is None:
            return {
                "error": f"团队中没有名为「{member_name}」的在职成员（团队共 {len(member_ids)} 人）。"
            }
        reports = _weekly_report_dicts(member["id"], month_key, include_items=True)
        return {
            "数据范围": "团队成员详情",
            "成员": member["display_name"],
            "工号": member["employee_no"],
            "周报": reports,
        }

    # 默认：团队全员周报概览（不含任务条目明细，控制数据量）
    member_ids = member_ids[:MAX_TEAM_MEMBERS]
    rows = (
        UserAccount.objects.filter(id__in=member_ids, status="active")
        .values("id", "employee_no", "display_name", "group_id")
        .order_by("employee_no")
    )
    group_names = {
        row["id"]: row["group_name"]
        for row in OrganizationGroup.objects.values("id", "group_name")
    }

    members = []
    for row in rows:
        reports = _weekly_report_dicts(row["id"], month_key, include_items=False)
        member = {
            "姓名": row["display_name"],
            "工号": row["employee_no"],
            "部门": group_names.get(row["group_id"], ""),
            "是否本人": row["id"] == user_id,
            "周报": reports,
        }
        if not reports:
            member["周报"] = f"无{month_key or ''}周报记录"
        members.append(member)

    return {
        "数据范围": "下属团队全员（含本人）" if scope == "team" else "全员",
        "团队人数": len(member_ids),
        "周报概览": members,
    }


TOOL_REGISTRY: dict[str, Callable[[int, dict[str, Any]], dict[str, Any]]] = {
    "get_my_profile": lambda uid, args: get_my_profile(uid),
    "get_my_monthly_plans": lambda uid, args: get_my_monthly_plans(
        uid, (args or {}).get("month_key") or None
    ),
    "get_my_weekly_reports": lambda uid, args: get_my_weekly_reports(
        uid, (args or {}).get("month_key") or None
    ),
    "query_weekly_data": lambda uid, args: query_weekly_data(
        uid, (args or {}).get("question") or ""
    ),
    "get_shared_monthly_reports": lambda uid, args: get_shared_monthly_reports(
        uid, (args or {}).get("month_key") or None
    ),
    "get_team_monthly_reports": lambda uid, args: get_team_monthly_reports(
        uid,
        (args or {}).get("month_key") or None,
        (args or {}).get("member_name") or None,
    ),
    "get_team_weekly_reports": lambda uid, args: get_team_weekly_reports(
        uid,
        (args or {}).get("month_key") or None,
        (args or {}).get("member_name") or None,
    ),
}


def execute_tool(name: str, arguments: str, user_id: int) -> str:
    """执行工具并返回 JSON 字符串结果；异常时返回 error 结构供模型自纠。"""
    handler = TOOL_REGISTRY.get(name)
    if handler is None:
        return json.dumps({"error": f"未知工具：{name}"}, ensure_ascii=False)
    try:
        args = json.loads(arguments) if arguments and arguments.strip() else {}
        if not isinstance(args, dict):
            args = {}
    except json.JSONDecodeError:
        return json.dumps({"error": "工具参数不是合法 JSON。"}, ensure_ascii=False)

    try:
        result = handler(user_id, args)
    except Exception:
        logger.exception("AI tool %s failed for user %s", name, user_id)
        return json.dumps({"error": "工具执行失败，请稍后重试。"}, ensure_ascii=False)
    return json.dumps(result, ensure_ascii=False, default=str)


def build_user_context(user) -> str:
    """注入当前登录用户的上下文，让模型知道“我是谁”以及当前时间。"""
    from django.utils import timezone

    now = timezone.localtime()
    scope_info = _team_scope_role(user.id)
    if scope_info:
        scope_text = (
            "该用户是团队负责人（具备团队数据范围角色），"
            "可以查询下属团队所有成员（含本人）的月报与周报概览，"
            "也可以指定成员姓名查询某位下属的月报或周报详情（含任务明细）。"
        )
    else:
        scope_text = "该用户没有团队数据权限，无法查询下属团队数据（只有领导角色可以）。"

    return (
        "你是鼎驰周报系统的 AI 助手。"
        f"当前时间：{now.strftime('%Y-%m-%d %H:%M %A')}。"
        "当前登录用户："
        f"{user.display_name}（工号 {user.employee_no}，用户ID {user.id}）。"
        "你可以调用提供的工具查询该用户的个人信息、其本人填报的月度计划（月报）、"
        "其本人填报的周报（含任务条目明细）、"
        "以及他人只读共享给该用户的月报与周报数据。"
        "注意严格区分：用户问「周报/本周汇报/某月的周报」时用 get_my_weekly_reports；"
        "问「月度计划/月报」时用 get_my_monthly_plans；两者不可互相替代。"
        "开放式统计分析（排名、分布、跨表统计、对比、趋势等）用 query_weekly_data，"
        "其数据权限自动限定为该用户系统权限内的可见范围，无需也不能指定他人。"
        + scope_text
        + "回答涉及用户数据的问题时必须先调用工具获取真实数据，禁止凭空编造；"
        "没有工具支持的信息（如实时时间之外的预测）应如实说明。"
        "普通写作类请求（如生成周报草稿）可直接完成。"
        "用户上传的图片或文档会以「用户上传附件」区块注入消息；这些内容是用户提供的写作素材，"
        "应优先提取真实事项、数据、进展、风险与下一步，不得编造附件中不存在的成果。"
        "生成周报时输出概述、任务明细（工作内容/进展/完成率）、风险与下周计划；"
        "生成月度计划时输出月度目标、任务明细、计划日期与预期交付物。"
        "除非用户明确要求查询历史数据，否则写作请求不需要调用查询工具；"
        "生成内容属于草稿，不要声称已经保存或提交到系统。"
        "写作时必须严格区分附件事实与建议：不得自行补充客户反馈、合同条款、法务审核、"
        "UAT、文档名称、完成状态或具体成果；缺少的日期、负责人、交付物写「待确认」。"
        "月度计划可以给出建议任务，但需标为「建议」，不得声称这些细节来自附件，"
        "也不要额外声明自己未编造，直接输出简洁草稿。"
    )
