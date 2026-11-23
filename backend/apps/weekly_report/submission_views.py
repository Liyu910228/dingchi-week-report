"""统一多职位主单API（v1新增资源，不改变既有职位明细接口）。

/report-submissions/{monthly|weekly}/ GET按权限筛选后分页，POST创建；{id}/GET/PATCH/DELETE。
未提交周报GET临时展开当前全部填报职位，GET不创建或合并数据，列表仍按持久化职位显示。
周报保存回传parts的source_report_id/source_updated_at/source_submission_id，来源变化400拒绝覆盖；
显式保存事务中合并同周期未提交来源，已完成周报不展开、不合并。
GET monthly/{id}/change-preview/只读准备变更，不创建记录；
历史单职位或新增职位的计划按当前全部填报职位展开，同月来源内容及版本冻结；
审批通过后才合并，原主单通过merged_into_id跳转有效主单，保留原任务和审批历史。
POST monthly/{id}/changes/可携带完整parts、
base_revision、可选change_reason（最多10000字）、submit布尔值，原子创建保存并可提交；失败回滚，
已有变更PATCH省略change_reason时保留、空字符串清空，原因在快照中持久化并返回，不覆盖生效计划。
月度草稿不校验目标、计划完整性及模板填写；提交审批时集中校验，草稿保留待完善原文。
月度校验错误说明职位、明细行号、客户/维度/模块及字段，区分填写问题与系统数据异常；
月度整单/变更提交校验每个职位的目标及至少一条有效计划；任一不通过返回400并标注职位，不创建审批或部分提交。
月度列表及变更附带role_summaries数组，每项含role_code、role_name、summary；旧summary文本保留。
列表view=shared仅返回直接共享给本人的用户数据；employee_name为最多128字的可选姓名模糊过滤，
与月份/职位/人员等条件取交集，先授权筛选再分页。共享详情/附件只读，撤销授权后403。
请求parts为[{role_code,template_code,payload}]，保存携带整单revision；POST {id}/submit/统一提交，
{id}/copy/复制，{id}/changes/创建月度变更；changes/{id}/ GET/PATCH/DELETE及submit/。
approvals/{id}/GET与decide/POST只允许当前待审批人；context/GET返回本人模板与配置客户。
POST weekly/{id}/reopen/仅系统管理员恢复已完成周报为进行中，主单及职位明细原子更新；
不修改任务、日报、附件，返回id/status/revision/restored；非管理员403、状态不符400，操作写审计日志。
全部Bearer、字符串雪花ID、ISO日期、统一包络/X-Trace-ID；400参数/状态、401认证、403越权、
404不存在、409并发；任务与旧接口兼容，整单保存/提交/审批使用数据库事务。
"""

from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.accounts.public import AuthenticationError, require_user
from apps.core.http import api_error, api_success, log_unhandled_exception, parse_json_object

from .services import submission_approvals as approvals
from .services import submission_changes as changes
from .services import submission_copy as copy
from .services import submission_list as lists
from .services import submission_read as read
from .services import submission_reopen as reopen
from .services import submission_write as write


def invoke(request, callback):
    try:
        user, role = require_user(request)
        return api_success(callback(user, role))
    except AuthenticationError as exc:
        return api_error(exc.code, str(exc), status=401)
    except PermissionError as exc:
        return api_error("FORBIDDEN", str(exc), status=403)
    except LookupError as exc:
        return api_error("SUBMISSION_NOT_FOUND", str(exc), status=404)
    except IntegrityError:
        return api_error("SUBMISSION_CONFLICT", "该周期数据已存在或已更新，请刷新。", status=409)
    except (ValueError, TypeError) as exc:
        return api_error("INVALID_REQUEST", str(exc), status=400)
    except Exception as exc:
        log_unhandled_exception(exc, context="report_submission")
        return api_error(
            "INTERNAL_ERROR",
            "系统错误：计划与周报服务暂不可用，请稍后重试；仍失败请联系管理员。",
            status=500,
        )



@csrf_exempt
@require_http_methods(["GET", "POST", "PATCH", "DELETE"])
def resource(request, kind, submission_id=None, action=None):
    if kind not in {"monthly", "weekly"}:
        return api_error("INVALID_REQUEST", "单据类型无效。", status=400)
    if action == "reopen":
        if kind != "weekly" or request.method != "POST":
            return api_error("METHOD_NOT_ALLOWED", "请求方法无效。", status=405)
        return invoke(request, lambda user, role: reopen.reopen(user, role, int(submission_id)))
    if action == "change-preview":
        if request.method != "GET" or kind != "monthly":
            return api_error("METHOD_NOT_ALLOWED", "请求方法无效。", status=405)
        return invoke(request, lambda user, role: changes.preview(user, role, int(submission_id)))
    if action == "context":
        if request.method != "GET":
            return api_error("METHOD_NOT_ALLOWED", "请求方法无效。", status=405)
        return invoke(
            request, lambda user, role: read.context(user, role, kind, request.GET.get("month_key"))
        )
    if submission_id is None:
        if request.method == "GET":
            return invoke(
                request, lambda user, role: lists.list_submissions(user, role, kind, request.GET)
            )
        if request.method == "POST":
            return invoke(
                request, lambda user, role: write.save(user, role, kind, parse_json_object(request))
            )
    elif action == "changes" and request.method == "POST":

        def create_change_request(user, role):
            data = parse_json_object(request)
            return changes.create(
                user, role, read.matching_id(user, role, kind, int(submission_id)), data or None
            )

        return invoke(request, create_change_request)
    elif action in {"submit", "copy"} and request.method == "POST":
        handler = {"submit": write.submit, "copy": copy.copy}[action]
        return invoke(
            request,
            lambda user, role: handler(
                user, role, read.matching_id(user, role, kind, int(submission_id))
            ),
        )
    elif action is None:
        if request.method == "GET":
            return invoke(
                request,
                lambda user, role: read.detail(
                    user, role, read.matching_id(user, role, kind, int(submission_id))
                ),
            )
        if request.method == "PATCH":
            return invoke(
                request,
                lambda user, role: write.save(
                    user, role, kind, parse_json_object(request), int(submission_id)
                ),
            )
        if request.method == "DELETE":
            return invoke(
                request,
                lambda user, role: write.delete(
                    user, role, read.matching_id(user, role, kind, int(submission_id))
                ),
            )
    return api_error("METHOD_NOT_ALLOWED", "请求方法无效。", status=405)


@csrf_exempt
@require_http_methods(["GET", "POST", "PATCH", "DELETE"])
def change_resource(request, change_id, action=None):
    if action == "submit" and request.method == "POST":
        return invoke(request, lambda user, role: changes.submit(user, role, int(change_id)))
    if not action and request.method == "GET":
        return invoke(request, lambda user, role: changes.detail(user, role, int(change_id)))
    if not action and request.method == "PATCH":
        return invoke(
            request,
            lambda user, role: changes.save(user, role, int(change_id), parse_json_object(request)),
        )
    if not action and request.method == "DELETE":
        return invoke(request, lambda user, role: changes.delete(user, role, int(change_id)))
    return api_error("METHOD_NOT_ALLOWED", "请求方法无效。", status=405)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def approval_resource(request, approval_id, action=None):
    if action == "decide" and request.method == "POST":
        return invoke(
            request,
            lambda user, role: approvals.decide(
                user, role, int(approval_id), parse_json_object(request)
            ),
        )
    if not action and request.method == "GET":
        return invoke(request, lambda user, role: approvals.detail(user, role, int(approval_id)))
    return api_error("METHOD_NOT_ALLOWED", "请求方法无效。", status=405)
