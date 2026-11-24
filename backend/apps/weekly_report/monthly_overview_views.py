"""月度周报只读接口。"""

from django.views.decorators.http import require_GET

from .services import monthly_overview
from .submission_views import invoke


@require_GET
def overview(request, employee_id=None, month_key=None):
    """GET /api/v1/monthly-weekly-reports/ 按人员/月分页；/{人员ID}/{YYYY-MM}/详情。

    Bearer认证、本人及组织可见范围；mine/members、月份、职位、人员姓名筛选；
    字符串ID、ISO时间、统一包络/X-Trace-ID；400参数、401未登录、403越权、404无数据。
    查询参数：view默认members（全部可见范围，mine仅本人），month_key可选YYYY-MM，role_code最长64字，
    employee_name可选最长128字；page默认1且>=1、page_size默认10范围1..100。
    列表data含items/total/page/page_size/total_pages；每项含人员ID/姓名、月度、职位名、
    week_count已填写周数、completed_count整周所有记录已提交的周数、updated_at带时区ISO时间。
    详情data含month_key/employee_id、monthly_parts（已生效计划，缺失标记monthly_approved=false）、
    weeks（周期升序，plan/parts保留原周报契约，sources为原周报字符串id/role_name）。
    只读幂等，不合并或新增周报；周报按month_key归属，跨月周不拆分；新增字段向后兼容。
    """
    if employee_id is not None:
        return invoke(
            request,
            lambda user, role: monthly_overview.detail(user, role, int(employee_id), month_key),
        )
    return invoke(request, lambda user, role: monthly_overview.list_months(user, role, request.GET))
