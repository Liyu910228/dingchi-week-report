"""待办v1兼容扩展：周报提醒按人员+周期合并，role_code为空表示跨职位。
周报target包含kind和period_start，不再携带职位；审批待办保留职位及原权限。
已读、总数及分页统一按合并后的待办计算，既有重复周报提醒保留历史并完成。
"""
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.accounts.public import require_user
from apps.accounts.services.auth import AuthenticationError
from apps.core.http import api_error, api_success, log_unhandled_exception

from .services import inbox, items


def invoke(request, callback):
    try:
        user, role_code = require_user(request)
        return api_success(callback(user, role_code))
    except AuthenticationError as exc:
        return api_error(exc.code, str(exc), status=401)
    except LookupError as exc:
        return api_error("TODO_NOT_FOUND", str(exc), status=404)
    except (ValueError, TypeError) as exc:
        return api_error("INVALID_REQUEST", str(exc), status=400)
    except Exception as exc:
        log_unhandled_exception(exc, context="todos")
        return api_error("INTERNAL_ERROR", "待办服务暂不可用。", status=500)


@require_GET
def list_view(request):
    """GET /api/v1/todos/?page=1，本人待办，每页10条，不重置已读。

    Bearer/trace，400/401/500，完整契约见 docs/todos-api.md。
    """
    return invoke(
        request, lambda user, role: inbox.list_for_user(user, role, int(request.GET.get("page", 1)))
    )


@csrf_exempt
@require_POST
def read_view(request, item_id):
    """POST /api/v1/todos/{id}/read/，本人标记已读，不完成业务。

    幂等，字符串ID，401/404，Bearer/trace，完整契约见 docs/todos-api.md。
    """
    return invoke(request, lambda user, role: items.mark_read(user.id, role, int(item_id)))
