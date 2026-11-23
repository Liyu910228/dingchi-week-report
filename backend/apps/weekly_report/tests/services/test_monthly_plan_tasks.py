from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from apps.weekly_report.models import MonthlyPlan, MonthlyPlanTask, WeeklyReport
from apps.weekly_report.services import reports
from apps.weekly_report.services.monthly_plan_tasks import (
    list_monthly_plan_tasks,
    save_monthly_plan_tasks,
    validate_report_monthly_data,
    validate_tasks,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "template,field,label",
    [
        ("delivery_specialist_v1", "customer_name", "客户"),
        ("delivery_assistant_v1", "customer_name", "客户"),
        ("ito_sales_v1", "customer_name", "维度"),
        ("innovation_sales_v1", "customer_name", "客户"),
        ("recruitment_v1", "dimension", "维度"),
    ],
)
def test_visible_scope_is_required(template, field, label):
    for value in [None, "", " "]:
        with pytest.raises(ValueError, match=label):
            validate_report_monthly_data("目标", [{field: value, "work_task": "计划"}], template)
    validate_report_monthly_data("目标", [{field: "已填写", "work_task": "计划"}], template)


def test_functional_template_accepts_null_scope_columns():
    task = MonthlyPlanTask.objects.create(
        employee_id=101,
        role_code="functional_group",
        month_key="2026-10",
        scope_name=None,
        work_task="职能计划",
    )
    task.refresh_from_db()
    assert task.scope_name is None
    validate_report_monthly_data(
        "目标",
        [
            {
                "customer_name": None,
                "dimension": None,
                "work_task": task.work_task,
            }
        ],
        "functional_group_v1",
    )


def save_tasks(employee_id=101, role_code="delivery_specialist", month_key="2026-10", tasks=None):
    save_monthly_plan_tasks(
        employee_id=employee_id,
        role_code=role_code,
        month_key=month_key,
        value=tasks if tasks is not None else [{"work_task": "本月工作任务"}],
    )


def test_monthly_tasks_are_shared_and_isolated_by_employee_role_month():
    save_tasks(tasks=[{"work_task": " 一 "}, {"work_task": "二"}])
    save_tasks(employee_id=102)
    save_tasks(role_code="recruitment")
    save_tasks(month_key="2026-11")
    items = list_monthly_plan_tasks(
        employee_id=101, role_code="delivery_specialist", month_key="2026-10"
    )
    assert [item["work_task"] for item in items] == ["一", "二"]
    assert [item["sort_order"] for item in items] == [0, 1]
    assert all(isinstance(item["id"], str) and item["id"].isdigit() for item in items)
    save_tasks(tasks=[])
    assert MonthlyPlanTask.objects.count() == 3


@pytest.mark.parametrize(
    "value",
    [
        None,
        {},
        "任务",
        [None],
        [{"work_task": 1}],
        [{"work_task": " "}],
        [{"work_task": "任务"}] * 201,
    ],
)
def test_invalid_tasks_do_not_remove_previous_data(value):
    save_tasks()
    with pytest.raises(ValueError):
        save_monthly_plan_tasks(
            employee_id=101, role_code="delivery_specialist", month_key="2026-10", value=value
        )
    assert MonthlyPlanTask.objects.get().work_task == "本月工作任务"


def test_maximum_task_length_and_count_are_accepted():
    save_tasks(tasks=[{"work_task": "客" * 10000}] * 200)
    assert MonthlyPlanTask.objects.count() == 200


def test_customer_is_saved_trimmed_and_legacy_payload_still_works():
    save_tasks(tasks=[{"customer_name": " 示例客户 ", "work_task": "任务"}])
    items = list_monthly_plan_tasks(
        employee_id=101, role_code="delivery_specialist", month_key="2026-10"
    )
    assert items[0]["customer_name"] == "示例客户"
    save_tasks(tasks=[{"customer_name": "客" * 255, "work_task": "任务"}])
    assert len(MonthlyPlanTask.objects.get().scope_name) == 255
    for customer in ["客" * 256, 123]:
        with pytest.raises(ValueError, match="月度计划客户"):
            save_tasks(tasks=[{"customer_name": customer, "work_task": "任务"}])
        assert len(MonthlyPlanTask.objects.get().scope_name) == 255
    save_tasks()
    assert MonthlyPlanTask.objects.get().scope_name is None


def test_recruitment_dimension_uses_shared_scope_column():
    save_tasks(
        role_code="recruitment", tasks=[{"dimension": " 总体目标 ", "work_task": "招聘计划"}]
    )
    task = MonthlyPlanTask.objects.get()
    assert task.scope_name == "总体目标"
    for value in [123, "维" * 256]:
        with pytest.raises(ValueError, match="客户/维度"):
            save_tasks(role_code="recruitment", tasks=[{"dimension": value, "work_task": "计划"}])
    assert MonthlyPlanTask.objects.get().scope_name == "总体目标"


@pytest.mark.parametrize("month_key", ["2026-00", "2026-13", "0000-01", "2026-1", "bad"])
def test_invalid_month_is_rejected(month_key):
    with pytest.raises(ValueError):
        save_tasks(month_key=month_key)


def test_locked_monthly_goal_does_not_lock_new_monthly_tasks():
    goal = MonthlyPlan.objects.create(
        employee_id=101, role_code="delivery_specialist", month_key="2026-10", summary="已锁定目标"
    )
    save_tasks()
    save_tasks(tasks=[{"work_task": "修改计划"}])
    goal.refresh_from_db()
    assert goal.summary == "已锁定目标"
    assert MonthlyPlanTask.objects.get().work_task == "修改计划"


@pytest.fixture
def report_context(monkeypatch):
    for role in [
        "delivery_specialist",
        "delivery_assistant",
        "recruitment",
        "ito_sales",
        "innovation_sales",
        "functional_group",
    ]:
        MonthlyPlan.objects.create(
            employee_id=101,
            role_code=role,
            month_key="2026-10",
            summary="月度目标",
            status="approved",
            template_code=f"{role}_v1",
        )
    monkeypatch.setattr(reports, "_current_period_start", lambda: date(2026, 10, 12))
    monkeypatch.setattr(reports, "_role_scope", lambda role: "self")
    monkeypatch.setattr(
        reports,
        "resolve_role_template",
        lambda role: {"template_code": f"{role}_v1", "tasks": [], "metrics": []},
    )
    monkeypatch.setattr(
        reports, "get_template_by_code", lambda *args, **kwargs: {"tasks": [], "metrics": []}
    )
    # 既有进度历史模型缺少迁移；该行为与本次独立月度计划无关。
    monkeypatch.setattr(reports, "_get_item_progress_state", lambda report_id: {})
    monkeypatch.setattr(reports, "_record_item_progress_history", lambda **kwargs: None)
    monkeypatch.setattr(
        reports, "get_report_detail", lambda **kwargs: {"report": {"id": str(kwargs["report_id"])}}
    )
    return SimpleNamespace(id=101, group_id=None)


def payload(day=12, **kwargs):
    start = date(2026, 10, day)
    return {
        "period_start": start.isoformat(),
        "period_end": (start + timedelta(days=6)).isoformat(),
        "items": [],
        "metrics": [],
        "attachments": [],
        "daily_tasks": [],
        **kwargs,
    }


@pytest.mark.parametrize(
    "role",
    [
        "delivery_specialist",
        "delivery_assistant",
        "recruitment",
        "ito_sales",
        "innovation_sales",
        "functional_group",
    ],
)
def test_report_save_reads_common_monthly_tasks_without_editing(report_context, role):
    save_tasks(role_code=role, tasks=[{"scope_name": "已审批范围", "work_task": "共用计划"}])
    first = reports.create_or_update_report(user=report_context, role_code=role, payload=payload())
    reports.create_or_update_report(user=report_context, role_code=role, payload=payload(19))
    reports.create_or_update_report(
        user=report_context, role_code=role, report_id=int(first["report"]["id"]), payload=payload()
    )
    assert WeeklyReport.objects.count() == 2
    assert MonthlyPlanTask.objects.get().work_task == "共用计划"


def test_report_and_monthly_tasks_rollback_together(report_context):
    save_tasks()
    with pytest.raises(ValueError):
        reports.create_or_update_report(
            user=report_context,
            role_code="delivery_specialist",
            payload=payload(monthly_plan_tasks=[{"work_task": ""}]),
        )
    assert not WeeklyReport.objects.exists()
    assert MonthlyPlanTask.objects.get().work_task == "本月工作任务"


def test_other_user_and_completed_report_cannot_change_monthly_tasks(report_context):
    save_tasks(tasks=[{"scope_name": "客户", "work_task": "原计划"}])
    first = reports.create_or_update_report(
        user=report_context, role_code="delivery_specialist", payload=payload()
    )
    report_id = int(first["report"]["id"])
    with pytest.raises(reports.ReportPermissionError):
        reports.create_or_update_report(
            user=SimpleNamespace(id=102, group_id=None),
            role_code="delivery_specialist",
            report_id=report_id,
            payload=payload(monthly_plan_tasks=[]),
        )
    WeeklyReport.objects.filter(id=report_id).update(status="completed")
    with pytest.raises(reports.ReportError):
        reports.create_or_update_report(
            user=report_context,
            role_code="delivery_specialist",
            report_id=report_id,
            payload=payload(monthly_plan_tasks=[]),
        )
    assert MonthlyPlanTask.objects.get().work_task == "原计划"


def test_manager_detail_reads_report_owner_role_month(monkeypatch):
    save_tasks()
    save_tasks(employee_id=202, role_code="recruitment")
    header = {
        "id": 9001,
        "employee_id": 101,
        "role_code": "delivery_specialist",
        "template_code": "delivery_specialist_v1",
        "month_key": "2026-10",
        "status": "in_progress",
        "period_start": date(2026, 10, 12),
    }
    monkeypatch.setattr(reports.dao, "get_report_header", lambda report_id: header)
    monkeypatch.setattr(reports, "_role_scope", lambda role: "team")
    monkeypatch.setattr(reports, "visible_employee_ids", lambda user, role: [101, 202])
    monkeypatch.setattr(reports, "get_template_by_code", lambda *args, **kwargs: {})
    monkeypatch.setattr(reports, "_serialize_report_row", lambda row: row)
    monkeypatch.setattr(reports.dao, "get_monthly_plan", lambda *args: None)
    for method in ["get_report_items", "get_report_metrics", "get_report_attachments"]:
        monkeypatch.setattr(reports.dao, method, lambda report_id: [])
    detail = reports.get_report_detail(
        user=SimpleNamespace(id=202), role_code="recruitment", report_id=9001
    )
    assert [task["work_task"] for task in detail["monthly_plan_tasks"]] == ["本月工作任务"]
    assert detail["monthly_plan_tasks"][0]["id"] == str(
        MonthlyPlanTask.objects.get(employee_id=101, role_code="delivery_specialist").id
    )
    monkeypatch.setattr(reports, "visible_employee_ids", lambda user, role: [202])
    with pytest.raises(reports.ReportPermissionError):
        reports.get_report_detail(
            user=SimpleNamespace(id=202), role_code="recruitment", report_id=9001
        )


@pytest.mark.parametrize("status", ["draft", "pending", "rejected", "deleted"])
def test_report_requires_approved_plan(report_context, status):
    MonthlyPlan.objects.filter(employee_id=101, role_code="delivery_specialist").update(
        status=status
    )
    with pytest.raises(ValueError, match="审批通过"):
        reports.create_or_update_report(
            user=report_context, role_code="delivery_specialist", payload=payload()
        )
    assert not WeeklyReport.objects.exists()


def test_report_cannot_write_monthly_content_even_when_approved(report_context):
    save_tasks(tasks=[{"scope_name": "客户", "work_task": "原计划"}])
    first = reports.create_or_update_report(
        user=report_context, role_code="delivery_specialist", payload=payload(summary="原周报")
    )
    with pytest.raises(reports.ReportError, match="仅展示"):
        reports.create_or_update_report(
            user=report_context,
            role_code="delivery_specialist",
            report_id=int(first["report"]["id"]),
            payload=payload(summary="不能保存", monthly_plan_tasks=[]),
        )
    assert WeeklyReport.objects.get().summary == "原周报"
    assert MonthlyPlanTask.objects.get().work_task == "原计划"


def test_report_rechecks_changed_period_month(report_context):
    with pytest.raises(ValueError, match="2026-11"):
        reports.create_or_update_report(
            user=report_context,
            role_code="delivery_specialist",
            payload={**payload(), "period_start": "2026-11-02", "period_end": "2026-11-08"},
        )
    assert not WeeklyReport.objects.exists()


def test_historical_report_checks_saved_month_instead_of_period_month(report_context):
    first = reports.create_or_update_report(
        user=report_context, role_code="delivery_specialist", payload=payload()
    )
    report = WeeklyReport.objects.get()
    report.month_key = "2026-09"
    report.save(update_fields=["month_key"])
    with pytest.raises(ValueError, match="2026-09"):
        reports.create_or_update_report(
            user=report_context,
            role_code="delivery_specialist",
            report_id=int(first["report"]["id"]),
            payload=payload(),
        )
    report.refresh_from_db()
    assert report.month_key == "2026-09"


@pytest.mark.parametrize("field", ["scope_group_key", "task_group_key"])
@pytest.mark.parametrize("value", ["", "x" * 129, 42, []])
def test_monthly_group_keys_reject_invalid_values(field, value):
    with pytest.raises(ValueError, match="分组标识"):
        validate_tasks([{"work_task": "工作任务", field: value}])


def test_monthly_grouped_fields_must_be_consistent():
    rows = [
        {"work_task": "任务一", "scope_name": "客户",
         "scope_group_key": "scope", "task_group_key": "task"},
        {"work_task": "任务二", "scope_name": "客户",
         "scope_group_key": "scope", "task_group_key": "task"},
    ]
    with pytest.raises(ValueError, match="工作任务内容不一致"):
        validate_tasks(rows)
    rows[1]["work_task"] = "任务一"
    rows[1]["scope_name"] = "另一个客户"
    with pytest.raises(ValueError, match="客户/维度内容不一致"):
        validate_tasks(rows)


@pytest.mark.parametrize("template,label", [
    ("delivery_specialist_v1", "客户"), ("delivery_assistant_v1", "客户"),
    ("recruitment_v1", "维度"), ("ito_sales_v1", "维度"),
    ("innovation_sales_v1", "客户"), ("human_resources_v1", "模块"),
    ("functional_group_v1", "客户"),
])
def test_task_validation_feedback_identifies_row_scope_field_and_system_issue(template, label):
    task = {"scope_name": "中信证券", "work_task": "新增需求", "task_source": "template",
            "task_template": "", "task_values": []}
    with pytest.raises(ValueError) as error:
        validate_tasks([{"scope_name": "正常", "work_task": "正常任务"}, task], template)
    message = str(error.value)
    assert "第2条" in message and f"{label}「中信证券」" in message
    assert "新增需求" in message and "系统错误" in message and "模板原文缺失" in message
    assert "重新选择模板" in message


@pytest.mark.parametrize("patch,reason", [
    ({"work_content": "长" * 10001}, "主要工作内容"),
    ({"output_description": "长" * 10001}, "输出成果"),
    ({"planned_date": "2026-02-30"}, "计划完成时间"),
    ({"work_task": ""}, "工作任务不能为空"),
])
def test_task_content_feedback_identifies_customer_and_invalid_field(patch, reason):
    with pytest.raises(ValueError) as error:
        validate_tasks([{"scope_name": "港交所", "work_task": "任务", **patch}],
                       "delivery_specialist_v1")
    message = str(error.value)
    assert "第1条" in message and "客户「港交所」" in message
    assert "填写内容校验不通过" in message and reason in message
    assert "系统错误" not in message


def test_template_fill_feedback_distinguishes_broken_structure_and_oversized_input():
    task = {"scope_name": "其他", "work_task": "任务", "task_source": "template",
            "task_template": "目标？", "task_values": None}
    with pytest.raises(ValueError, match="系统错误.*填充值数据缺失或格式异常"):
        validate_tasks([task])
    task["task_values"] = ["长" * 257]
    with pytest.raises(ValueError, match="填写内容校验不通过.*256") as error:
        validate_tasks([task])
    assert "系统错误" not in str(error.value)
