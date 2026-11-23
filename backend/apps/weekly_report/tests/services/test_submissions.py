"""多职位主单事务、审批隔离与客户权限的回归。"""

from copy import deepcopy
from datetime import date, timedelta

import pytest
from django.utils import timezone

from apps.accounts.models import Role, UserRole
from apps.accounts.services.monthly_approvers import set_monthly_approvers
from apps.approvals.models import ApprovalRequest
from apps.weekly_report.models import MonthlyPlan, WeeklyReport
from apps.weekly_report.services import reports
from apps.weekly_report.services import submission_approvals as approvals
from apps.weekly_report.services import submission_changes as changes
from apps.weekly_report.services import submission_copy as copies
from apps.weekly_report.services import submission_list as lists
from apps.weekly_report.services import submission_read as read
from apps.weekly_report.services import submission_write as write
from apps.weekly_report.submission_models import ReportSubmission
from apps.weekly_report.tests.services.test_monthly_plan_workflow import people as people

pytestmark = pytest.mark.django_db


@pytest.fixture
def multi(people, monkeypatch):
    owner = people[0]
    role = Role.objects.create(
        role_code="sales",
        role_name="销售",
        scope="self",
        report_template_code="delivery_specialist_v1",
    )
    UserRole.objects.create(user_id=owner.id, role_id=role.id)
    monkeypatch.setattr(
        reports,
        "get_template_by_code",
        lambda code, **kwargs: {"template_code": code, "fields": [], "tasks": [], "metrics": []},
    )
    monkeypatch.setattr(
        reports,
        "resolve_role_template",
        lambda role: reports.get_template_by_code("delivery_specialist_v1"),
    )
    return people


def body(month="2026-11"):
    return {
        "month_key": month,
        "parts": [
            {
                "role_code": code,
                "template_code": "delivery_specialist_v1",
                "payload": {
                    "summary": "目标",
                    "tasks": [{"scope_name": "客户", "work_task": "任务", "work_content": "内容"}],
                },
            }
            for code in ["delivery", "sales"]
        ],
    }


def test_atomic_drafts_aggregate_and_authorization(multi):
    owner, _, _, outsider = multi
    invalid = body()
    invalid["parts"][1]["payload"]["tasks"] = "bad-structure"
    with pytest.raises(ValueError):
        write.save(owner, "delivery", "monthly", invalid)
    assert not MonthlyPlan.objects.filter(employee_id=owner.id).exists()
    assert not ReportSubmission.objects.exists()
    data = write.save(owner, "delivery", "monthly", body())
    assert len(data["parts"]) == 2
    assert data["plan"]["role_name"] == "delivery / 销售"
    rows = lists.list_submissions(
        owner, "delivery", "monthly", {"view": "mine", "page_size": 1, "role_code": "sales"}
    )
    assert rows["total"] == 1 and len(rows["items"]) == 1
    assert len(set(p["id"] for p in data["parts"])) == 2
    with pytest.raises(PermissionError):
        write.save(outsider, "leader", "monthly", body(), int(data["plan"]["id"]))
    omitted = body()
    omitted["parts"].pop()
    with pytest.raises(ValueError):
        write.save(owner, "delivery", "monthly", omitted)


def approve(multi, data):
    owner, first, second, _ = multi
    data = write.submit(owner, "delivery", int(data["plan"]["id"]))
    aid = int(data["approvals"][0]["id"])
    assert ApprovalRequest.objects.filter(business_type="monthly_submission").count() == 1
    assert not lists.list_submissions(second, "manager", "monthly", {"view": "approvals"})[
        "approvals"
    ]
    with pytest.raises(PermissionError):
        approvals.detail(second, "manager", aid)
    with pytest.raises(PermissionError):
        approvals.decide(second, "manager", aid, {"action": "approve"})
    approvals.decide(first, "manager", aid, {"action": "approve"})
    assert lists.list_submissions(second, "manager", "monthly", {"view": "approvals"})["total"] == 1
    assert approvals.detail(second, "manager", aid)["id"] == str(aid)
    return approvals.decide(second, "manager", aid, {"action": "approve"})


def test_one_approval_and_copy_uses_effective_parts(multi):
    owner = multi[0]
    data = approve(multi, write.save(owner, "delivery", "monthly", body()))
    assert data["plan"]["status"] == "approved"
    assert set(MonthlyPlan.objects.values_list("status", flat=True)) == {"approved"}
    change = changes.create(owner, "delivery", int(data["plan"]["id"]))
    proposal = deepcopy(change["snapshot"])
    proposal["revision"] = change["change"]["revision"]
    proposal["parts"][1]["payload"]["summary"] = "未生效新目标"
    changes.save(owner, "delivery", int(change["change"]["id"]), proposal)
    copied = copies.copy(owner, "delivery", int(data["plan"]["id"]))
    assert copied["plan"]["status"] == "draft" and copied["plan"]["month_key"] == "2026-12"
    assert all(p["payload"]["summary"] == "目标" for p in copied["parts"])
    old_ids = {t["id"] for p in data["parts"] for t in p["payload"]["tasks"]}
    assert old_ids.isdisjoint({t["id"] for p in copied["parts"] for t in p["payload"]["tasks"]})


def test_autoapprove_change_publish_and_stale_revision(multi):
    owner = multi[0]
    set_monthly_approvers(owner.id, [])
    data = write.save(owner, "delivery", "monthly", body())
    sid = int(data["plan"]["id"])
    data = write.submit(owner, "delivery", sid)
    change = changes.create(owner, "delivery", sid)
    proposal = deepcopy(change["snapshot"])
    proposal["revision"] = 0
    proposal["parts"][0]["payload"]["summary"] = "生效新目标"
    change = changes.save(owner, "delivery", int(change["change"]["id"]), proposal)
    changes.submit(owner, "delivery", int(change["change"]["id"]))
    assert read.detail(owner, "delivery", sid)["parts"][0]["payload"]["summary"] == "生效新目标"
    with pytest.raises(ValueError):
        changes.save(owner, "delivery", int(change["change"]["id"]), proposal)


def test_weekly_atomic_gate_and_independent_parts(multi):
    owner = multi[0]
    set_monthly_approvers(owner.id, [])
    start = timezone.localdate()
    start -= timedelta(days=start.weekday())
    monthly = write.save(owner, "delivery", "monthly", body(start.strftime("%Y-%m")))
    write.submit(owner, "delivery", int(monthly["plan"]["id"]))
    payload = {
        "period_start": start.isoformat(),
        "parts": [
            {"role_code": code, "payload": {"items": [], "metrics": [], "daily_tasks": []}}
            for code in ["delivery", "sales"]
        ],
    }
    MonthlyPlan.objects.filter(employee_id=owner.id, role_code="sales").update(status="draft")
    with pytest.raises(ValueError, match="审批"):
        write.save(owner, "delivery", "weekly", payload)
    assert not WeeklyReport.objects.exists()
    assert not ReportSubmission.objects.filter(kind="weekly").exists()
    MonthlyPlan.objects.filter(employee_id=owner.id, role_code="sales").update(status="approved")
    data = write.save(owner, "delivery", "weekly", payload)
    assert len(data["parts"]) == 2 and data["plan"]["status"] == "in_progress"
    WeeklyReport.objects.filter(id=data["parts"][0]["id"]).update(summary="keep")
    payload["revision"] = data["plan"]["revision"]
    payload["parts"][0]["payload"]["summary"] = "changed"
    payload["parts"][1]["payload"]["items"] = [
        {"task_code": "bad", "progress_percent": "not-a-number"}
    ]
    with pytest.raises(ValueError):
        write.save(owner, "delivery", "weekly", payload, int(data["plan"]["id"]))
    assert WeeklyReport.objects.get(id=data["parts"][0]["id"]).summary == "keep"


def test_old_write_cannot_split_unified_and_legacy_ids_remain_readable(multi):
    from apps.weekly_report.services.monthly_plans import write as old_write

    owner = multi[0]
    data = write.save(owner, "delivery", "monthly", body())
    child = data["parts"][0]
    with pytest.raises(ValueError, match="统一"):
        old_write.save(
            owner,
            "delivery",
            {**child["payload"], "revision": child["payload"]["revision"]},
            int(child["id"]),
        )
    old = old_write.save(
        owner,
        "delivery",
        {
            "month_key": "2026-12",
            "summary": "旧版",
            "tasks": [{"scope_name": "客户", "work_task": "任务"}],
        },
    )
    restored = read.detail(owner, "delivery", int(old["plan"]["id"]))
    assert restored["plan"]["legacy"] and restored["parts"][0]["id"] == old["plan"]["id"]
    assert restored["plan"]["id"] != old["plan"]["id"]
    assert lists.list_submissions(owner, "delivery", "monthly", {"view": "mine"})["total"] == 2


def test_customer_ids_persist_in_monthly_metadata_and_weekly_rows(multi):
    from apps.dictionary.models import DictionaryItem

    owner = multi[0]
    set_monthly_approvers(owner.id, [])
    customer = DictionaryItem.objects.create(dict_type="customer", dict_code="c", dict_name="客户")
    start = timezone.localdate()
    start -= timedelta(days=start.weekday())
    payload = body(start.strftime("%Y-%m"))
    payload["parts"][0]["payload"]["tasks"][0]["customer_id"] = str(customer.id)
    monthly = write.save(owner, "delivery", "monthly", payload)
    assert monthly["parts"][0]["payload"]["tasks"][0]["customer_id"] == str(customer.id)
    write.submit(owner, "delivery", int(monthly["plan"]["id"]))
    weekly = {
        "period_start": start.isoformat(),
        "parts": [
            {
                "role_code": code,
                "payload": {
                    "items": [
                        {
                            "task_code": "custom",
                            "customer_id": str(customer.id),
                            "task_name_snapshot": "事项",
                        }
                    ],
                    "metrics": [],
                    "daily_tasks": [],
                },
            }
            for code in ["delivery", "sales"]
        ],
    }
    data = write.save(owner, "delivery", "weekly", weekly)
    assert all(p["detail"]["items"][0]["customer_id"] == str(customer.id) for p in data["parts"])


def test_moving_weekly_period_preserves_daily_entries(multi):
    owner = multi[0]
    set_monthly_approvers(owner.id, [])
    end = timezone.localdate()
    end -= timedelta(days=end.weekday())
    start = end - timedelta(days=7)
    for month in {start.strftime("%Y-%m"), end.strftime("%Y-%m")}:
        monthly = write.save(owner, "delivery", "monthly", body(month))
        write.submit(owner, "delivery", int(monthly["plan"]["id"]))
    initial = {
        "period_start": start.isoformat(),
        "parts": [
            {
                "role_code": code,
                "payload": {
                    "items": [], "metrics": [],
                    "daily_tasks": [{
                        "work_date": (start + timedelta(days=index)).isoformat(),
                        "work_content": f"日报{index}",
                    }],
                },
            }
            for index, code in enumerate(["delivery", "sales"])
        ],
    }
    saved = write.save(owner, "delivery", "weekly", initial)
    daily_ids = [part["payload"]["daily_tasks"][0]["id"] for part in saved["parts"]]
    for part in saved["parts"]:
        task = part["payload"]["daily_tasks"][0]
        task["work_date"] = (date.fromisoformat(task["work_date"]) + timedelta(days=7)).isoformat()
    moved = write.save(owner, "delivery", "weekly", {
        "period_start": end.isoformat(),
        "revision": saved["plan"]["revision"],
        "parts": saved["parts"],
    }, int(saved["plan"]["id"]))
    assert [part["payload"]["daily_tasks"][0]["id"] for part in moved["parts"]] == daily_ids
    assert [part["payload"]["daily_tasks"][0]["work_date"] for part in moved["parts"]] == [
        end.isoformat(), (end + timedelta(days=1)).isoformat()
    ]


def test_rejection_only_requires_changing_one_position(multi):
    owner, first, _, _ = multi
    data = write.save(owner, "delivery", "monthly", body())
    sid = int(data["plan"]["id"])
    data = write.submit(owner, "delivery", sid)
    approvals.decide(
        first,
        "manager",
        int(data["approvals"][0]["id"]),
        {"action": "reject", "reason": "修改销售目标"},
    )
    rejected = read.detail(owner, "delivery", sid)
    payload = {
        "month_key": rejected["plan"]["month_key"],
        "revision": rejected["plan"]["revision"],
        "parts": rejected["parts"],
    }
    unchanged = write.save(owner, "delivery", "monthly", payload, sid)
    payload["revision"] = unchanged["plan"]["revision"]
    payload["parts"][1]["payload"]["summary"] = "已修改销售目标"
    saved = write.save(owner, "delivery", "monthly", payload, sid)
    assert saved["plan"]["status"] == "draft"
    assert write.submit(owner, "delivery", sid)["plan"]["status"] == "pending"


def test_recreating_deleted_monthly_plan_keeps_approval_history_and_position_filter(multi):
    owner, first, _, _ = multi
    original = write.save(owner, "delivery", "monthly", body())
    sid = int(original["plan"]["id"])
    submitted = write.submit(owner, "delivery", sid)
    approval_id = int(submitted["approvals"][0]["id"])
    rejected = approvals.decide(
        first, "manager", approval_id, {"action": "reject", "reason": "修改目标"}
    )
    payload = body()
    payload["revision"] = rejected["plan"]["revision"]
    payload["parts"][0]["payload"]["summary"] = "修改后草稿"
    write.save(owner, "delivery", "monthly", payload, sid)
    write.delete(owner, "delivery", sid)
    write.save(owner, "delivery", "monthly", body())

    result = lists.list_submissions(
        first, "manager", "monthly", {"view": "approvals", "role_code": "sales"}
    )
    assert result["total"] == 1
    assert result["approvals"][0]["id"] == str(approval_id)
    assert result["approvals"][0]["role_name"] == "delivery / 销售"
    assert result["approvals"][0]["snapshot"]["parts"][0]["payload"]["summary"] == "目标"


def test_monthly_status_filter_includes_change_children(multi):
    owner = multi[0]
    set_monthly_approvers(owner.id, [])
    data = write.save(owner, "delivery", "monthly", body())
    write.submit(owner, "delivery", int(data["plan"]["id"]))
    changes.create(owner, "delivery", int(data["plan"]["id"]))
    rows = lists.list_submissions(owner, "delivery", "monthly", {"view": "mine", "status": "draft"})
    assert rows["total"] == 1 and rows["items"][0]["status"] == "approved"
    assert rows["items"][0]["children"][0]["status"] == "draft"


def test_main_http_contract_and_kind_boundary(multi, client):
    from apps.core.authentication.token import create_access_token

    owner = multi[0]
    path = "/api/v1/report-submissions/monthly/"
    assert client.get(path).status_code == 401
    client.defaults["HTTP_AUTHORIZATION"] = "Bearer " + create_access_token(
        user_id=int(owner.id), role_code="delivery"
    )
    created = client.post(
        path, body(), content_type="application/json", HTTP_X_TRACE_ID="submission-test"
    )
    assert created.status_code == 200, created.content
    assert created["X-Trace-ID"] == "submission-test"
    data = created.json()["data"]
    assert isinstance(data["plan"]["id"], str) and len(data["parts"]) == 2
    assert client.get(path, {"view": "mine", "role_code": "sales"}).json()["data"]["total"] == 1
    assert client.get(f"/api/v1/report-submissions/weekly/{data['plan']['id']}/").status_code == 404
    assert client.get(path, {"period_start": "invalid-date"}).status_code == 400
    invalid = {**body(), "revision": -1}
    assert (
        client.patch(
            path + data["plan"]["id"] + "/", invalid, content_type="application/json"
        ).status_code
        == 400
    )


def test_copy_weekly_all_positions_new_text_ids_without_daily(multi):
    from apps.weekly_report.models import WeeklyReportDailyTask

    owner = multi[0]
    set_monthly_approvers(owner.id, [])
    start = timezone.localdate()
    start -= timedelta(days=start.weekday())
    for month in {start.strftime("%Y-%m"), (start + timedelta(days=7)).strftime("%Y-%m")}:
        monthly = write.save(owner, "delivery", "monthly", body(month))
        write.submit(owner, "delivery", int(monthly["plan"]["id"]))
    parts = [
        {
            "role_code": code,
            "payload": {
                "items": [
                    {
                        "task_code": "custom",
                        "task_name_snapshot": "独立任务",
                        "work_content": "独立工作内容",
                        "output_description": "成果",
                        "customer_name_snapshot": "客户",
                    }
                ],
                "metrics": [],
                "attachments": [],
                "daily_tasks": [{"work_date": start.isoformat(), "work_content": "不复制的日报"}],
            },
        }
        for code in ["delivery", "sales"]
    ]
    data = write.save(
        owner, "delivery", "weekly", {"period_start": start.isoformat(), "parts": parts}
    )
    sid = int(data["plan"]["id"])
    ReportSubmission.objects.filter(id=sid).update(status="completed")
    WeeklyReport.objects.filter(submission_id=sid).update(status="completed")
    copied = copies.copy(owner, "delivery", sid)
    assert len(copied["parts"]) == 2 and copied["plan"]["id"] != data["plan"]["id"]
    assert all(not part["detail"]["daily_tasks"] for part in copied["parts"])
    assert WeeklyReportDailyTask.objects.count() == 2
    old = {
        item[key]
        for part in data["parts"]
        for item in part["detail"]["items"]
        for key in ["id", "task_text_id", "work_content_text_id"]
    }
    new = {
        item[key]
        for part in copied["parts"]
        for item in part["detail"]["items"]
        for key in ["id", "task_text_id", "work_content_text_id"]
    }
    assert old.isdisjoint(new)


def test_legacy_weekly_detail_uses_root_revision_and_position_tabs(multi):
    owner = multi[0]
    start = timezone.localdate() - timedelta(days=timezone.localdate().weekday())
    root = ReportSubmission.objects.create(
        kind="weekly",
        employee_id=owner.id,
        month_key=start.strftime("%Y-%m"),
        period_start=start,
        period_end=start + timedelta(days=6),
        status="in_progress",
        legacy=True,
        revision=3,
    )
    report = WeeklyReport.objects.create(
        employee_id=owner.id,
        role_code="delivery",
        template_code="delivery_specialist_v1",
        month_key=root.month_key,
        period_start=start,
        period_end=root.period_end,
        as_of_date=start,
        status="in_progress",
        submission_id=root.id,
    )
    result = read.detail(owner, "delivery", root.id)
    assert result["plan"]["revision"] == 3
    assert [part["role_code"] for part in result["parts"]] == ["delivery", "sales"]
    assert result["parts"][0]["id"] == str(report.id)
    assert result["can_edit"]


def test_weekly_context_keeps_approved_role_gate_independent(multi):
    owner = multi[0]
    MonthlyPlan.objects.create(
        employee_id=owner.id,
        role_code="delivery",
        month_key="2026-10",
        template_code="delivery_specialist_v1",
        status="approved",
        summary="目标",
    )
    config = read.context(owner, "delivery", "weekly", "2026-10")
    positions = {part["role_code"]: part for part in config["positions"]}
    assert positions["delivery"]["monthly_approved"]
    assert not positions["sales"]["monthly_approved"]
    assert positions["delivery"]["monthly_message"] == ""


def test_monthly_list_preserves_separate_role_goals_and_change_snapshot(multi):
    import json

    from apps.weekly_report.submission_models import ReportSubmissionChange

    owner = multi[0]
    payload = body()
    payload["parts"][0]["payload"]["summary"] = "交付目标第一行\n交付目标第二行"
    payload["parts"][1]["payload"]["summary"] = "销售目标\n金额目标"
    data = write.save(owner, "delivery", "monthly", payload)
    result = lists.list_submissions(owner, "delivery", "monthly", {"view": "mine"})
    sections = result["items"][0]["role_summaries"]
    assert sections == [
        {
            "role_code": "delivery",
            "role_name": "delivery",
            "summary": "交付目标第一行\n交付目标第二行",
        },
        {"role_code": "sales", "role_name": "销售", "summary": "销售目标\n金额目标"},
    ]
    snapshot = {"summary": "原兼容摘要", "parts": data["parts"]}
    change = ReportSubmissionChange.objects.create(
        submission_id=int(data["plan"]["id"]),
        base_revision=0,
        base_snapshot_json=json.dumps(snapshot),
        proposed_snapshot_json=json.dumps(snapshot),
    )
    changed = read.serialize_change(change)
    assert changed["role_summaries"] == sections
    assert changed["summary"] == "原兼容摘要"


@pytest.mark.parametrize("position", [0, 1])
@pytest.mark.parametrize("missing", ["summary", "tasks"])
def test_monthly_submit_requires_every_position_complete(multi, position, missing):
    owner = multi[0]
    payload = body()
    payload["parts"][position]["payload"][missing] = "  \n " if missing == "summary" else []
    data = write.save(owner, "delivery", "monthly", payload)
    sid = int(data["plan"]["id"])
    label = "delivery" if position == 0 else "销售"
    message = "请填写月度目标" if missing == "summary" else "请至少填写一条月度计划"
    with pytest.raises(ValueError, match=f"{label}：{message}"):
        write.submit(owner, "delivery", sid)
    assert ReportSubmission.objects.get(id=sid).status == "draft"
    assert not MonthlyPlan.objects.filter(submission_id=sid).exclude(status="draft").exists()
    assert not ApprovalRequest.objects.filter(business_id=sid).exists()


def test_monthly_submit_reports_all_missing_positions_without_partial_approval(multi):
    owner = multi[0]
    payload = body()
    for part in payload["parts"]:
        part["payload"].update(summary="", tasks=[])
    data = write.save(owner, "delivery", "monthly", payload)
    sid = int(data["plan"]["id"])
    with pytest.raises(ValueError) as error:
        write.submit(owner, "delivery", sid)
    assert "delivery：请填写月度目标；请至少填写一条月度计划" in str(error.value)
    assert "销售：请填写月度目标；请至少填写一条月度计划" in str(error.value)
    assert not ApprovalRequest.objects.filter(business_id=sid).exists()
    fixed = body()
    fixed["revision"] = data["plan"]["revision"]
    write.save(owner, "delivery", "monthly", fixed, sid)
    assert write.submit(owner, "delivery", sid)["plan"]["status"] == "pending"


def test_change_preview_is_readonly_and_explicit_save_creates_once(multi):
    from apps.weekly_report.submission_models import ReportSubmissionChange

    owner = multi[0]
    sid = int(write.save(owner, "delivery", "monthly", body())["plan"]["id"])
    write.submit(owner, "delivery", sid)
    approvals.decide(
        multi[1],
        "manager",
        int(read.detail(owner, "delivery", sid)["approvals"][0]["id"]),
        {"action": "approve"},
    )
    approvals.decide(
        multi[2],
        "manager",
        int(read.detail(owner, "delivery", sid)["approvals"][0]["id"]),
        {"action": "approve"},
    )
    before = ReportSubmissionChange.objects.count()
    preview = changes.preview(owner, "delivery", sid)
    assert preview["change"]["id"] == "" and preview["can_edit"]
    assert ReportSubmissionChange.objects.count() == before
    changes.preview(owner, "delivery", sid)
    assert ReportSubmissionChange.objects.count() == before
    payload = {
        "parts": preview["snapshot"]["parts"],
        "base_revision": preview["plan"]["revision"],
        "change_reason": "业务计划调整",
    }
    saved = changes.create(owner, "delivery", sid, payload)
    assert saved["snapshot"]["change_reason"] == "业务计划调整"
    assert ReportSubmissionChange.objects.count() == before + 1
    cid = int(saved["change"]["id"])
    payload["revision"] = saved["change"]["revision"]
    payload["change_reason"] = "补充说明"
    again = changes.save(owner, "delivery", cid, payload)
    assert again["change"]["id"] == saved["change"]["id"]
    assert again["snapshot"]["change_reason"] == "补充说明"
    assert ReportSubmissionChange.objects.count() == before + 1
    assert read.detail(owner, "delivery", sid)["parts"][0]["payload"]["summary"] == "目标"


def test_explicit_change_create_rolls_back_invalid_input_and_stale_version(multi):
    from apps.weekly_report.submission_models import ReportSubmissionChange

    owner = multi[0]
    sid = int(write.save(owner, "delivery", "monthly", body())["plan"]["id"])
    parent = ReportSubmission.objects.get(id=sid)
    parent.status = "approved"
    parent.save()
    MonthlyPlan.objects.filter(submission_id=sid).update(status="approved")
    preview = changes.preview(owner, "delivery", sid)
    payload = {
        "parts": preview["snapshot"]["parts"],
        "base_revision": parent.revision,
        "change_reason": "x" * 10001,
    }
    with pytest.raises(ValueError, match="变更原因"):
        changes.create(owner, "delivery", sid, payload)
    assert not ReportSubmissionChange.objects.exists()
    payload.update(change_reason="", base_revision=parent.revision + 1)
    with pytest.raises(ValueError, match="版本已变更"):
        changes.create(owner, "delivery", sid, payload)
    assert not ReportSubmissionChange.objects.exists()
    payload["base_revision"] = parent.revision
    payload["submit"] = True
    with pytest.raises(ValueError, match="修改内容"):
        changes.create(owner, "delivery", sid, payload)
    assert not ReportSubmissionChange.objects.exists()
    payload["parts"][0]["payload"]["summary"] = "调整后的目标"
    payload["change_reason"] = "资源调整"
    result = changes.create(owner, "delivery", sid, payload)
    assert result["change"]["status"] == "pending"
    assert result["approvals"][0]["snapshot"]["change_reason"] == "资源调整"


def test_change_preview_api_get_never_creates_draft(client, multi):
    from unittest.mock import patch

    from apps.weekly_report.submission_models import ReportSubmissionChange

    owner = multi[0]
    sid = int(write.save(owner, "delivery", "monthly", body())["plan"]["id"])
    ReportSubmission.objects.filter(id=sid).update(status="approved")
    MonthlyPlan.objects.filter(submission_id=sid).update(status="approved")
    with patch(
        "apps.weekly_report.submission_views.require_user", return_value=(owner, "delivery")
    ):
        for _ in range(2):
            response = client.get(f"/api/v1/report-submissions/monthly/{sid}/change-preview/")
            assert response.status_code == 200
            assert response.json()["data"]["change"]["id"] == ""
        assert not ReportSubmissionChange.objects.exists()
        response = client.post(
            f"/api/v1/report-submissions/monthly/{sid}/changes/",
            data="bad-json",
            content_type="application/json",
        )
        assert response.status_code == 400
        assert not ReportSubmissionChange.objects.exists()


def approved_legacy_month(owner, people, code, month="2026-10"):
    from apps.weekly_report.services.monthly_plans import write as old_write

    data = old_write.save(
        owner,
        code,
        {
            "month_key": month,
            "summary": f"{code}旧目标",
            "tasks": [{"scope_name": "客户", "work_task": f"{code}旧任务"}],
        },
    )
    pid = int(data["plan"]["id"])
    old_write.submit(owner, code, pid)
    for manager in people[1:3]:
        old_write.decide(manager, "manager", pid, {"action": "approve"})
    return MonthlyPlan.objects.get(id=pid)


def test_legacy_change_expands_missing_position_and_merges_only_after_approval(multi):
    from apps.weekly_report.submission_models import ReportSubmissionChange

    owner = multi[0]
    original = approved_legacy_month(owner, multi, "delivery")
    sid = original.submission_id
    preview = changes.preview(owner, "delivery", sid)
    assert [part["role_code"] for part in preview["snapshot"]["parts"]] == ["delivery", "sales"]
    added = preview["snapshot"]["parts"][1]
    assert added["payload"] == {"summary": "", "tasks": []}
    assert MonthlyPlan.objects.filter(employee_id=owner.id, month_key="2026-10").count() == 1
    assert not ReportSubmissionChange.objects.exists()
    added["payload"] = {
        "summary": "销售新目标",
        "tasks": [{"scope_name": "客户", "work_task": "销售新任务"}],
    }
    payload = {
        "parts": preview["snapshot"]["parts"],
        "base_revision": preview["change"]["base_revision"],
    }
    saved = changes.create(owner, "delivery", sid, payload)
    cid = int(saved["change"]["id"])
    changes.submit(owner, "delivery", cid)
    assert MonthlyPlan.objects.filter(employee_id=owner.id, month_key="2026-10").count() == 1
    for manager in multi[1:3]:
        aid = int(changes.detail(owner, "delivery", cid)["approvals"][0]["id"])
        approvals.decide(manager, "manager", aid, {"action": "approve"})
    result = read.detail(owner, "delivery", sid)
    assert len(result["parts"]) == 2 and not result["plan"]["legacy"]
    assert MonthlyPlan.objects.get(id=original.id).submission_id == sid
    assert (
        MonthlyPlan.objects.get(
            employee_id=owner.id, role_code="sales", month_key="2026-10"
        ).summary
        == "销售新目标"
    )
    assert len(result["history"]) >= 2


def test_legacy_same_month_sources_merge_without_losing_ids_or_approval_history(multi):
    owner = multi[0]
    first = approved_legacy_month(owner, multi, "delivery")
    second = approved_legacy_month(owner, multi, "sales")
    old_root = second.submission_id
    approval_ids = set(ApprovalRequest.objects.values_list("id", flat=True))
    preview = changes.preview(owner, "delivery", first.submission_id)
    assert preview["snapshot"]["parts"][1]["payload"]["summary"] == "sales旧目标"
    preview["snapshot"]["parts"][0]["payload"]["summary"] = "变更后目标"
    set_monthly_approvers(owner.id, [])
    result = changes.create(
        owner,
        "delivery",
        first.submission_id,
        {
            "parts": preview["snapshot"]["parts"],
            "base_revision": preview["change"]["base_revision"],
            "submit": True,
        },
    )
    assert result["change"]["status"] == "approved"
    second.refresh_from_db()
    assert second.submission_id == first.submission_id
    assert second.summary == "sales旧目标"
    assert ReportSubmission.objects.get(id=old_root).merged_into_id == first.submission_id
    assert read.detail(owner, "delivery", old_root)["plan"]["id"] == str(first.submission_id)
    assert (
        lists.list_submissions(
            owner, "delivery", "monthly", {"view": "mine", "month_key": "2026-10"}
        )["total"]
        == 1
    )
    assert approval_ids <= set(ApprovalRequest.objects.values_list("id", flat=True))
    assert len(read.detail(owner, "delivery", old_root)["history"]) >= 3


def test_legacy_history_position_uses_frozen_name_after_role_rename(multi):
    owner = multi[0]
    plan = approved_legacy_month(owner, multi, "delivery")
    Role.objects.filter(role_code="delivery").update(role_name="已改名职位")
    result = read.detail(owner, "delivery", plan.submission_id)
    assert result["history"][0]["role_code"] == "delivery"
    assert result["history"][0]["role_name"] == "delivery"
    assert result["history"][0]["snapshot"]["role_name"] == "delivery"


def legacy_week(owner, code, start):
    root = ReportSubmission.objects.create(
        kind="weekly", employee_id=owner.id, month_key=start.strftime("%Y-%m"),
        period_start=start, period_end=start + timedelta(days=6),
        status="in_progress", legacy=True,
    )
    return WeeklyReport.objects.create(
        submission_id=root.id, employee_id=owner.id, role_code=code,
        template_code="delivery_specialist_v1", month_key=root.month_key,
        period_start=start, period_end=root.period_end, as_of_date=start,
        status="in_progress", summary=f"{code}原内容",
    )


def test_weekly_read_expands_without_writes_and_save_merges(multi, monkeypatch):
    owner = multi[0]
    monkeypatch.setattr(reports, "ensure_approved", lambda *args: None)
    start = reports._current_period_start() - timedelta(days=7)
    first = legacy_week(owner, "delivery", start)
    second = legacy_week(owner, "sales", start)
    from apps.weekly_report.models import WeeklyReportDailyTask

    daily = WeeklyReportDailyTask.objects.create(
        report_id=second.id, work_date=start, work_content="原始日报内容",
    )
    old_root = second.submission_id
    before = list(WeeklyReport.objects.values())
    data = read.detail(owner, "delivery", first.submission_id)
    assert len(data["parts"]) == 2
    assert list(WeeklyReport.objects.values()) == before
    assert data["plan"]["role_codes"] == ["delivery"]
    payload = {"period_start": start.isoformat(), "revision": data["plan"]["revision"],
               "parts": data["parts"]}
    saved = write.save(owner, "delivery", "weekly", payload, first.submission_id)
    assert saved["plan"]["role_codes"] == ["delivery", "sales"]
    second.refresh_from_db()
    assert second.submission_id == first.submission_id and second.summary == "sales原内容"
    assert ReportSubmission.objects.get(id=old_root).merged_into_id == first.submission_id
    daily.refresh_from_db()
    assert daily.report_id == second.id and daily.work_content == "原始日报内容"


def test_weekly_missing_position_is_temporary_until_save_and_completed_stays_single(
    multi, monkeypatch
):
    owner = multi[0]
    monkeypatch.setattr(reports, "ensure_approved", lambda *args: None)
    start = reports._current_period_start() - timedelta(days=14)
    first = legacy_week(owner, "delivery", start)
    data = read.detail(owner, "delivery", first.submission_id)
    assert len(data["parts"]) == 2 and data["parts"][1]["payload"]["items"] == []
    assert WeeklyReport.objects.count() == 1
    with pytest.raises(ValueError, match="全部职位"):
        write.submit(owner, "delivery", first.submission_id)
    WeeklyReport.objects.filter(id=first.id).update(status="completed")
    assert len(read.detail(owner, "delivery", first.submission_id)["parts"]) == 1
    WeeklyReport.objects.filter(id=first.id).update(status="in_progress")
    data = read.detail(owner, "delivery", first.submission_id)
    payload = {"period_start": start.isoformat(), "revision": data["plan"]["revision"],
               "parts": data["parts"]}
    saved = write.save(owner, "delivery", "weekly", payload, first.submission_id)
    assert len(saved["parts"]) == 2 and WeeklyReport.objects.count() == 2


def test_weekly_stale_source_rejects_and_rolls_back_merge(multi):
    owner = multi[0]
    first = legacy_week(owner, "delivery", reports._current_period_start())
    data = read.detail(owner, "delivery", first.submission_id)
    legacy_week(owner, "sales", first.period_start)
    with pytest.raises(ValueError, match="已更新"):
        write.save(owner, "delivery", "weekly", {
            "period_start": first.period_start.isoformat(),
            "revision": data["plan"]["revision"], "parts": data["parts"],
        }, first.submission_id)
    assert not ReportSubmission.objects.filter(merged_into_id__isnull=False).exists()



def test_submit_error_identifies_position_customer_and_broken_template_after_draft_save(multi):
    payload = body()
    payload["parts"][1]["payload"]["tasks"][0].update(
        scope_name="港交所", task_source="template", task_template="", task_values=[]
    )
    saved = write.save(multi[0], "delivery", "monthly", payload)
    sid = int(saved["plan"]["id"])
    with pytest.raises(ValueError) as error:
        write.submit(multi[0], "delivery", sid)
    message = str(error.value)
    assert "销售" in message and "第1条" in message and "港交所" in message
    assert "系统错误" in message and "模板原文缺失" in message
    assert ReportSubmission.objects.get(id=sid).status == "draft"
    assert not ApprovalRequest.objects.exists()



def test_incomplete_monthly_draft_round_trip_and_submit_only_validation(multi):
    payload = body()
    payload["parts"][0]["payload"] = {"summary": "", "tasks": []}
    payload["parts"][1]["payload"] = {"summary": "销售目标", "tasks": [
        {"scope_name": "客户", "work_task": "", "work_content": "待补充",
         "task_source": "template", "task_template": "", "task_values": None,
         "planned_date": "2026-02-30"},
    ]}
    saved = write.save(multi[0], "delivery", "monthly", payload)
    sid = int(saved["plan"]["id"])
    loaded = read.detail(multi[0], "delivery", sid)
    assert loaded["parts"][0]["payload"]["summary"] == ""
    assert loaded["parts"][0]["payload"]["tasks"] == []
    task = loaded["parts"][1]["payload"]["tasks"][0]
    assert task["work_task"] == "" and task["work_content"] == "待补充"
    assert task["planned_date"] == "2026-02-30" and task["task_values"] is None
    with pytest.raises(ValueError) as error:
        write.submit(multi[0], "delivery", sid)
    assert "月度目标" in str(error.value) and "销售" in str(error.value)
    assert not ApprovalRequest.objects.exists()


def test_change_draft_keeps_incomplete_content_until_submission(multi):
    owner = multi[0]
    original = write.save(owner, "delivery", "monthly", body())
    sid = int(original["plan"]["id"])
    ReportSubmission.objects.filter(id=sid).update(status="approved")
    MonthlyPlan.objects.filter(submission_id=sid).update(status="approved")
    preview = changes.preview(owner, "delivery", sid)
    preview["snapshot"]["parts"][0]["payload"] = {"summary": "", "tasks": []}
    created = changes.create(owner, "delivery", sid, {
        "base_revision": preview["plan"]["revision"], "parts": preview["snapshot"]["parts"],
    })
    cid = int(created["change"]["id"])
    assert created["change"]["status"] == "draft"
    assert created["snapshot"]["parts"][0]["payload"]["summary"] == ""
    with pytest.raises(ValueError, match="月度目标"):
        changes.submit(owner, "delivery", cid)
    assert ReportSubmission.objects.get(id=sid).status == "approved"
    assert read.detail(owner, "delivery", sid)["parts"][0]["payload"]["summary"] == "目标"
