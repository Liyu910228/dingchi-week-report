"""Configurable weekly-report tables with logical relationships only."""

from django.db import models

from apps.core.models.base import SnowflakeIdModel


class ReportTemplate(SnowflakeIdModel):
    template_code = models.CharField(max_length=64)
    template_name = models.CharField(max_length=128)
    description = models.CharField(max_length=500, blank=True, default="")
    status = models.CharField(max_length=16, default="active")
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "report_template"
        constraints = [
            models.UniqueConstraint(
                fields=["template_code"],
                name="uq_report_template_code",
            ),
        ]
        ordering = ["template_code"]


class ReportTemplateItem(SnowflakeIdModel):
    template_id = models.BigIntegerField()
    section_code = models.CharField(max_length=64)
    section_name = models.CharField(max_length=128)
    task_code = models.CharField(max_length=64)
    label = models.CharField(max_length=255)
    guidance = models.CharField(max_length=500, blank=True, default="")
    item_type = models.CharField(max_length=16, default="task")
    scope_type = models.CharField(max_length=16, default="overall")
    value_type = models.CharField(max_length=16, default="text")
    unit = models.CharField(max_length=32, blank=True, default="")
    required = models.BooleanField(default=False)
    validation_rule = models.CharField(max_length=255, blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0)
    config_json = models.TextField(blank=True, default="{}")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "report_template_item"
        constraints = [
            models.UniqueConstraint(
                fields=["template_id", "task_code"],
                name="uq_report_template_item_code",
            ),
        ]
        ordering = ["sort_order", "id"]


class WeeklyReport(SnowflakeIdModel):
    submission_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    role_code = models.CharField(max_length=64)
    template_code = models.CharField(max_length=64)
    employee_id = models.BigIntegerField()
    group_id = models.BigIntegerField(null=True, blank=True)
    period_type = models.CharField(max_length=16, default="week")
    month_key = models.CharField(max_length=7)
    period_start = models.DateField()
    period_end = models.DateField()
    as_of_date = models.DateField()
    # 状态持久化保存：not_started/in_progress/completed；提交只由用户手动触发。
    status = models.CharField(max_length=24, default="in_progress")
    summary = models.TextField(blank=True, default="")
    risk_level = models.CharField(max_length=16, default="none")
    risk_blocked = models.BooleanField(default=False)
    risk_reason = models.TextField(blank=True, default="")
    next_action = models.TextField(blank=True, default="")
    support_needed = models.TextField(blank=True, default="")
    expected_resolve_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "weekly_report"
        constraints = [
            models.UniqueConstraint(
                fields=["employee_id", "role_code", "period_start"],
                name="uq_weekly_report_employee_role_period",
            ),
        ]
        ordering = ["-period_start", "-updated_at"]


class MonthlyPlan(SnowflakeIdModel):
    submission_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    role_code = models.CharField(max_length=64)
    employee_id = models.BigIntegerField()
    group_id = models.BigIntegerField(null=True, blank=True)
    month_key = models.CharField(max_length=7)
    summary = models.TextField(blank=True, default="")
    template_code = models.CharField(max_length=64, blank=True, default="")
    status = models.CharField(max_length=16, default="draft")
    revision = models.PositiveIntegerField(default=0)
    rejection_reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "monthly_plan"
        constraints = [
            models.UniqueConstraint(
                fields=["employee_id", "role_code", "month_key"],
                name="uq_monthly_plan_employee_role_month",
            ),
        ]
        ordering = ["-month_key", "-updated_at"]


class MonthlyPlanChange(SnowflakeIdModel):
    """已生效月度计划的变更子流程，审批前不覆盖主流程数据。"""

    monthly_plan_id = models.BigIntegerField()
    base_revision = models.PositiveIntegerField()
    base_snapshot_json = models.TextField()
    proposed_snapshot_json = models.TextField()
    published_snapshot_json = models.TextField(blank=True, default="")
    effective_revision = models.PositiveIntegerField(default=0)
    revision = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, default="draft")
    rejection_reason = models.TextField(blank=True, default="")
    created_by = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "monthly_plan_change"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["monthly_plan_id", "created_at"], name="idx_monthly_change_root")
        ]


class MonthlyPlanRevision(SnowflakeIdModel):
    monthly_plan_id = models.BigIntegerField()
    revision = models.PositiveIntegerField()
    changed_by = models.BigIntegerField()
    action = models.CharField(max_length=16)
    snapshot_json = models.TextField()
    changes_json = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "monthly_plan_revision"
        ordering = ["-revision", "-id"]


class MonthlyPlanTask(SnowflakeIdModel):
    """同一员工、角色、月份共用的月度计划任务，不与周工作任务混存。"""

    employee_id = models.BigIntegerField()
    role_code = models.CharField(max_length=64)
    month_key = models.CharField(max_length=7)
    scope_name = models.CharField(max_length=255, blank=True, null=True, default="")
    work_task = models.TextField()
    work_content = models.TextField(blank=True, default="")
    output_description = models.TextField(blank=True, default="")
    planned_date = models.DateField(null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "monthly_plan_task"
        constraints = [
            models.UniqueConstraint(
                fields=["employee_id", "role_code", "month_key", "sort_order"],
                name="uq_monthly_plan_task_order",
            ),
        ]
        ordering = ["sort_order", "id"]


class MonthlyPlanTaskProgress(SnowflakeIdModel):
    """提交后仍可维护的执行进度；计划基线与审批快照保持不变。"""

    task_id = models.BigIntegerField(unique=True)
    data_json = models.TextField(blank=True, default="{}")
    revision = models.PositiveIntegerField(default=0)
    updated_by = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "monthly_plan_task_progress"
        ordering = ["-updated_at", "-id"]


class MonthlyPlanTaskProgressHistory(SnowflakeIdModel):
    """实时进度每次有效变更的完整前后值，独立于计划审批版本。"""

    task_id = models.BigIntegerField(db_index=True)
    revision = models.PositiveIntegerField()
    changed_by = models.BigIntegerField()
    before_json = models.TextField(blank=True, default="{}")
    after_json = models.TextField(blank=True, default="{}")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "monthly_plan_task_progress_history"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["task_id", "created_at"], name="idx_mptph_task_time"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["task_id", "revision"], name="uq_mptph_task_revision"),
        ]


class WeeklyTaskText(SnowflakeIdModel):
    """周报内共享的长文本；逻辑关联，不创建数据库外键。"""

    report_id = models.BigIntegerField()
    content_type = models.CharField(max_length=24)
    content = models.TextField(blank=True, default="")
    source = models.CharField(max_length=16, default="custom")
    template_text = models.TextField(blank=True, default="")
    values_json = models.TextField(blank=True, default="[]")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "weekly_task_text"


class WeeklyReportItem(SnowflakeIdModel):
    report_id = models.BigIntegerField()
    scope_type = models.CharField(max_length=16, default="overall")
    customer_id = models.BigIntegerField(null=True, blank=True)
    customer_name_snapshot = models.CharField(max_length=255, blank=True, default="")
    section_code = models.CharField(max_length=64)
    task_code = models.CharField(max_length=64)
    task_name_snapshot = models.TextField(blank=True, default="")
    customer_text_id = models.BigIntegerField(null=True, blank=True)
    dimension_text_id = models.BigIntegerField(null=True, blank=True)
    task_text_id = models.BigIntegerField(null=True, blank=True)
    work_content_text_id = models.BigIntegerField(null=True, blank=True)
    guidance_snapshot = models.CharField(max_length=500, blank=True, default="")
    work_content = models.TextField(blank=True, default="")
    output_description = models.TextField(blank=True, default="")
    planned_completion_date = models.DateField(null=True, blank=True)
    progress_text = models.TextField(blank=True, default="")
    progress_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    quality_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    on_time_status = models.CharField(max_length=24, default="in_progress")
    actual_completion_date = models.DateField(null=True, blank=True)
    delay_reason = models.TextField(blank=True, default="")
    next_action = models.TextField(blank=True, default="")
    expected_completion_date = models.DateField(null=True, blank=True)
    owner_id = models.BigIntegerField(null=True, blank=True)
    owner_name_snapshot = models.CharField(max_length=128, blank=True, default="")
    collaborator_names = models.CharField(max_length=500, blank=True, default="")
    document_links = models.TextField(blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "weekly_report_item"
        ordering = ["sort_order", "id"]


class WeeklyReportItemProgressHistory(SnowflakeIdModel):
    """任务进度历史快照；通过逻辑 ID 关联周报和任务，不建立数据库外键。"""

    report_id = models.BigIntegerField()
    report_item_id = models.BigIntegerField()
    task_code_snapshot = models.CharField(max_length=64)
    progress_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    quality_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    on_time_status = models.CharField(max_length=24, default="in_progress")
    record_date = models.DateField()
    recorded_by = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "weekly_report_item_progress_history"
        indexes = [
            models.Index(fields=["report_id", "record_date"], name="idx_wriph_report_date"),
            models.Index(
                fields=["report_id", "task_code_snapshot", "created_at"],
                name="idx_wriph_task_time",
            ),
        ]
        ordering = ["record_date", "created_at", "id"]


class WeeklyReportMetric(SnowflakeIdModel):
    report_id = models.BigIntegerField()
    item_id = models.BigIntegerField(null=True, blank=True)
    metric_code = models.CharField(max_length=64)
    metric_name_snapshot = models.CharField(max_length=255)
    value_type = models.CharField(max_length=16, default="number")
    target_value_decimal = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    actual_value_decimal = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    value_text = models.TextField(blank=True, default="")
    unit = models.CharField(max_length=32, blank=True, default="")
    precision = models.PositiveSmallIntegerField(default=0)
    baseline_value_decimal = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "weekly_report_metric"
        ordering = ["metric_code", "id"]


class WeeklyReportDailyTask(SnowflakeIdModel):
    """日报记录；与周报通过逻辑 report_id 关联，不建立数据库外键。"""

    report_id = models.BigIntegerField()
    work_date = models.DateField()
    work_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "weekly_report_daily_task"
        constraints = [
            models.UniqueConstraint(
                fields=["report_id", "work_date"],
                name="uq_weekly_report_daily_task_date",
            ),
        ]
        ordering = ["work_date", "id"]


from .submission_models import ReportSubmission, ReportSubmissionChange  # noqa: E402,F401
