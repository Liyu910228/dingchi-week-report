from django.urls import path

from . import monthly_plan_management_views as monthly_views
from . import submission_views, views
from .monthly_plan_task_views import monthly_plan_task_list_view, monthly_plan_task_progress_view

app_name = "weekly_report"

urlpatterns = [
    path("report-submissions/approvals/<str:approval_id>/", submission_views.approval_resource),
    path(
        "report-submissions/approvals/<str:approval_id>/decide/",
        submission_views.approval_resource,
        {"action": "decide"},
    ),
    path("report-submissions/changes/<str:change_id>/", submission_views.change_resource),
    path(
        "report-submissions/changes/<str:change_id>/submit/",
        submission_views.change_resource,
        {"action": "submit"},
    ),
    path(
        "report-submissions/<str:kind>/context/", submission_views.resource, {"action": "context"}
    ),
    path("report-submissions/<str:kind>/", submission_views.resource),
    path("report-submissions/<str:kind>/<str:submission_id>/", submission_views.resource),
    path(
        "report-submissions/<str:kind>/<str:submission_id>/<str:action>/", submission_views.resource
    ),
    path(
        "monthly-plan-management/<str:plan_id>/copy/", monthly_views.copy_view, name="monthly-copy"
    ),
    path(
        "monthly-plan-management/approvals/<str:approval_id>/", monthly_views.approval_detail_view
    ),
    path(
        "monthly-plan-management/<str:plan_id>/changes/",
        monthly_views.create_change_view,
        name="monthly-change-create",
    ),
    path(
        "monthly-plan-management/changes/<str:change_id>/",
        monthly_views.change_detail_view,
        name="monthly-change-detail",
    ),
    path(
        "monthly-plan-management/changes/<str:change_id>/submit/",
        monthly_views.change_submit_view,
        name="monthly-change-submit",
    ),
    path(
        "monthly-plan-management/changes/<str:change_id>/decide/",
        monthly_views.change_decide_view,
        name="monthly-change-decide",
    ),
    path("monthly-plan-management/context/", monthly_views.context_view, name="monthly-context"),
    path(
        "monthly-plan-management/gate/<str:month_key>/",
        monthly_views.gate_view,
        name="monthly-gate",
    ),
    path("monthly-plan-management/", monthly_views.list_view, name="monthly-list"),
    path(
        "monthly-plan-management/<str:plan_id>/submit/",
        monthly_views.submit_view,
        name="monthly-submit",
    ),
    path(
        "monthly-plan-management/<str:plan_id>/decide/",
        monthly_views.decide_view,
        name="monthly-decide",
    ),
    path(
        "monthly-plan-management/<str:plan_id>/", monthly_views.detail_view, name="monthly-detail"
    ),
    path(
        "attachments/",
        views.pending_attachment_upload_view,
        name="pending-attachment-upload",
    ),
    path(
        "attachments/<str:attachment_id>/",
        views.attachment_delete_view,
        name="attachment-delete",
    ),
    path(
        "attachments/<str:attachment_id>/download/",
        views.attachment_download_view,
        name="attachment-download",
    ),
    path("dashboard/summary/", views.dashboard_view, name="dashboard"),
    path("dashboard/next-week/", views.dashboard_next_week_view, name="dashboard-next-week"),
    path("weekly-report-templates/<str:template_code>/", views.template_view, name="template"),
    path("monthly-plans/<str:month_key>/", views.monthly_plan_view, name="monthly-plan"),
    path(
        "monthly-plan-tasks/<str:task_id>/progress/",
        monthly_plan_task_progress_view,
        name="monthly-plan-task-progress",
    ),
    path(
        "monthly-plan-tasks/<str:month_key>/",
        monthly_plan_task_list_view,
        name="monthly-plan-tasks",
    ),
    path("weekly-reports/", views.report_list_view, name="list"),
    path(
        "weekly-reports/<str:report_id>/daily-tasks/",
        views.daily_task_list_view,
        name="daily-task-list",
    ),
    path(
        "weekly-reports/<str:report_id>/daily-tasks/<str:daily_task_id>/",
        views.daily_task_detail_view,
        name="daily-task-detail",
    ),
    path(
        "weekly-reports/<str:report_id>/submit/",
        views.report_submit_view,
        name="submit",
    ),
    path("weekly-reports/<str:report_id>/copy/", views.report_copy_view, name="copy"),
    path("weekly-reports/<str:report_id>/", views.report_detail_view, name="detail"),
]
