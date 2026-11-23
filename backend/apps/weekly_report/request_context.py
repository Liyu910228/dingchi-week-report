"""周报/月度计划HTTP填写上下文；X-Report-Role仅接受本人有效职位。

所有v1报告接口兼容无此请求头；列表/审批聚合所有可见职位，新增使用显式职位，
已有本人记录优先使用记录职位。越权职位403，Bearer认证401，保留统一trace。
"""

from apps.accounts.public import require_user

from .services.reporting_role import resolve_reporting_role


def require_report_user(request):
    user, default_role = require_user(request)
    selected = str(request.headers.get("X-Report-Role", "")).strip()
    match = getattr(request, "resolver_match", None)
    identifiers = match.kwargs if match else {}
    role = resolve_reporting_role(user, default_role, selected, identifiers)
    if (
        request.method == "GET"
        and not identifiers
        and match
        and match.url_name
        in {
            "list",
            "monthly-list",
            "dashboard",
            "dashboard-next-week",
        }
    ):
        role = default_role
    return user, role
