"""MCP 工具：按调用方数据范围查询周报数据。

依赖（仅读取，不修改）：apps.weekly_report.dao、apps.mcp_server.security、
apps.mcp_server.utils.date_scope。
"""
from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from apps.mcp_server.header_auth import MCP_API_KEY_VAR
from apps.mcp_server.security import (
    get_caller_by_api_key,
    resolve_owner_id,
    resolve_visible_employee_ids,
)
from apps.mcp_server.utils.date_scope import resolve_period
from apps.weekly_report.dao import get_report_items, list_monthly_plans, list_reports


def register(server: MCPServer) -> None:
    @server.tool()
    def query_weekly_report(
        owner: str = "",
        year: int | None = None,
        month: int | None = None,
        week: int | None = None,
        day: str = "",
        status: str = "",
        include_items: bool = False,
    ) -> dict[str, Any]:
        """按调用方的数据范围查询鼎驰周报系统的周报数据，返回 JSON。

        工具/入口：query_weekly_report，经统一 MCP HTTP 入口 /mcp/ 调用。
        认证：密钥通过 HTTP 头传入（X-MCP-API-Key，或 Authorization: Bearer），
             由 config/asgi.py 的 McpApiKeyMiddleware 提取后存入 ContextVar；
             后端按密钥定位调用用户，并依据其角色 scope（个人/团队/领导）判定
             可见的周报数据范围。工具参数中不再需要传 mcp_api_key。
        请求参数：
          - owner：可选，按 username/employee_no/display_name 限定某人；
                   缺省表示查询「数据范围内的全部」周报。
          - year/month/week/day：时间范围；优先级 day > week > month > 默认本周。
            未给任何时间则默认今年本月本周；仅给 month 表示整月。
          - status：可选，按周报状态过滤（not_started/in_progress/completed）。
          - include_items：可选，是否一并返回周报明细条目，默认 false。
        成功响应：{ ok:true, scope, caller, query, total, reports:[...], monthly_plans:[...] }。
             monthly_plans 为范围内各员工当月的月度计划（月度目标，来自 monthly_plan 表）。
        失败响应：{ ok:false, error, message }。
        """
        mcp_api_key = MCP_API_KEY_VAR.get()
        if not mcp_api_key:
            return {
                "ok": False,
                "error": "missing_api_key",
                "message": "缺少 X-MCP-API-Key 请求头（或 Authorization: Bearer）。",
            }
        caller = get_caller_by_api_key(mcp_api_key)
        if caller is None:
            return {
                "ok": False,
                "error": "invalid_api_key",
                "message": "mcp_api_key 无效或对应账户非 active。",
            }

        _scope_code, scope_label, visible_ids = resolve_visible_employee_ids(caller["id"])

        owner_id = None
        owner_name = None
        if owner:
            owner_id = resolve_owner_id(owner)
            if owner_id is None:
                return {
                    "ok": False,
                    "error": "owner_not_found",
                    "message": f"未找到用户：{owner}",
                }
            if owner_id not in visible_ids:
                return {
                    "ok": False,
                    "error": "forbidden",
                    "message": "该用户不在你的数据范围内。",
                }
            employee_ids = [owner_id]
            owner_name = owner
        else:
            employee_ids = visible_ids

        period = resolve_period(year=year, month=month, week=week, day=day or None)

        rows = list_reports(
            employee_ids=employee_ids,
            month_key=period["month_key"] if period["mode"] == "month" else None,
            period_start=period["period_start"],
            period_end=period["period_end"],
            status=status or None,
        )

        reports: list[dict[str, Any]] = []
        for r in rows:
            item = dict(r)
            if include_items:
                item["items"] = get_report_items(item["id"])
            reports.append(item)

        monthly_plans = list_monthly_plans(
            employee_ids=employee_ids,
            month_key=period.get("month_key"),
        )
        name_by_id = {r["employee_id"]: r.get("employee_name") for r in rows}
        for mp in monthly_plans:
            mp["employee_name"] = name_by_id.get(mp["employee_id"])

        return {
            "ok": True,
            "scope": scope_label,
            "caller": {
                "employee_no": caller["employee_no"],
                "display_name": caller["display_name"],
            },
            "query": {
                "owner_filter": owner_name,
                "period": period,
                "status_filter": status or None,
            },
            "total": len(reports),
            "reports": reports,
            "monthly_plans": monthly_plans,
        }
