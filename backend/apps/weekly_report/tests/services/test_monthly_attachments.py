"""月度附件在七类模板中的保存、权限、审批历史及独立复制回归。"""

from copy import deepcopy

import pytest
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import Role, UserAccount, UserRole
from apps.accounts.services.monthly_approvers import set_monthly_approvers
from apps.core.models import Attachment
from apps.weekly_report.models import MonthlyPlan
from apps.weekly_report.services import reports
from apps.weekly_report.services.monthly_plans import change_write, read, write
from apps.weekly_report.services.monthly_plans.copy import copy_next_month
from apps.weekly_report.tests.services.test_monthly_plan_workflow import people as people

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    settings.ATTACHMENT_ALLOWED_EXTENSIONS = []
    return tmp_path


def upload(user, name="evidence.txt"):
    return reports.upload_pending_report_attachment(
        user=user, uploaded_file=SimpleUploadedFile(name, b"evidence", content_type="text/plain")
    )


def payload(file, month="2026-10"):
    return {
        "month_key": month,
        "summary": "目标",
        "tasks": [
            {
                "scope_name": "范围",
                "work_task": "任务",
                "document_links": "资料说明\nhttps://example.test/doc",
                "attachments": [
                    {"id": file["id"], "description": "材料说明", "file_name": "伪造的名称"}
                ],
            }
        ],
    }


@pytest.mark.parametrize(
    "template",
    [
        "delivery_specialist_v1",
        "delivery_assistant_v1",
        "recruitment_v1",
        "ito_sales_v1",
        "innovation_sales_v1",
        "functional_group_v1",
        "human_resources_v1",
    ],
)
def test_save_and_approval_snapshot_all_templates(people, monkeypatch, template):
    owner = people[0]
    monkeypatch.setattr(reports, "resolve_role_template", lambda role: {"template_code": template})
    file = upload(owner)
    data = write.save(owner, "delivery", payload(file))
    task = data["tasks"][0]
    attachment = Attachment.objects.get(id=file["id"])
    assert (
        attachment.attachment_type == "monthly_plan"
        and str(attachment.relation_id) == data["plan"]["id"]
    )
    assert task["attachments"][0]["file_name"] == "evidence.txt"
    assert task["attachments"][0]["description"] == "材料说明"
    submitted = write.submit(owner, "delivery", int(data["plan"]["id"]))
    assert submitted["approvals"][0]["snapshot"]["tasks"][0]["attachments"] == task["attachments"]
    assert (
        reports.get_report_attachment_for_download(
            user=owner, role_code="delivery", attachment_id=attachment.id
        ).id
        == attachment.id
    )


def test_download_permissions_and_reject_foreign_pending(people):
    owner = people[0]
    outsider = UserAccount.objects.create(
        username="other",
        employee_no="OTHER",
        display_name="other",
        password_ciphertext="test-password",
    )
    UserRole.objects.create(user_id=outsider.id, role_id=Role.objects.get(role_code="delivery").id)
    file = upload(owner)
    data = write.save(owner, "delivery", payload(file))
    with pytest.raises(PermissionError):
        reports.get_report_attachment_for_download(
            user=outsider, role_code="delivery", attachment_id=int(file["id"])
        )
    foreign = upload(outsider, "other.txt")
    with pytest.raises(PermissionError):
        write.save(owner, "delivery", payload(foreign, "2026-11"))
    with pytest.raises(PermissionError):
        write.save(owner, "delivery", payload(file, "2026-11"))
    assert MonthlyPlan.objects.filter(employee_id=owner.id).count() == 1
    assert (
        read.detail(owner, "delivery", int(data["plan"]["id"]))["tasks"][0]["attachments"][0]["id"]
        == file["id"]
    )


def test_remove_in_change_preserves_effective_plan_and_history(people):
    owner = people[0]
    set_monthly_approvers(owner.id, [])
    file = upload(owner)
    data = write.save(owner, "delivery", payload(file))
    pid = int(data["plan"]["id"])
    write.submit(owner, "delivery", pid)
    change = change_write.create(owner, "delivery", pid)
    proposal = deepcopy(change["snapshot"])
    proposal["revision"] = change["change"]["revision"]
    proposal["tasks"][0]["attachments"] = []
    saved = change_write.save(owner, "delivery", int(change["change"]["id"]), proposal)
    assert read.detail(owner, "delivery", pid)["tasks"][0]["attachments"]
    change_write.submit(owner, "delivery", int(saved["change"]["id"]))
    assert read.detail(owner, "delivery", pid)["tasks"][0]["attachments"] == []
    assert (
        change_write.change_read.detail(owner, "delivery", int(saved["change"]["id"]))[
            "base_snapshot"
        ]["tasks"][0]["attachments"][0]["id"]
        == file["id"]
    )
    assert default_storage.exists(Attachment.objects.get(id=file["id"]).storage_key)


def test_copy_creates_independent_attachment_and_file(people):
    owner = people[0]
    set_monthly_approvers(owner.id, [])
    file = upload(owner)
    data = write.save(owner, "delivery", payload(file))
    pid = int(data["plan"]["id"])
    write.submit(owner, "delivery", pid)
    copied = copy_next_month(owner, "delivery", pid)
    item = copied["tasks"][0]["attachments"][0]
    assert item["id"] != file["id"] and item["description"] == "材料说明"
    source = Attachment.objects.get(id=file["id"])
    target = Attachment.objects.get(id=item["id"])
    assert source.storage_key != target.storage_key and target.relation_id == int(
        copied["plan"]["id"]
    )
    with default_storage.open(target.storage_key, "rb") as stream:
        assert stream.read() == b"evidence"


def test_omitted_field_in_old_payload_preserves_files(people):
    owner = people[0]
    file = upload(owner)
    data = write.save(owner, "delivery", payload(file))
    task = dict(data["tasks"][0])
    task.pop("attachments")
    task["work_task"] = "修改任务"
    saved = write.save(
        owner,
        "delivery",
        {
            "month_key": "2026-10",
            "summary": "目标",
            "tasks": [task],
            "revision": data["plan"]["revision"],
        },
        int(data["plan"]["id"]),
    )
    assert saved["tasks"][0]["attachments"][0]["id"] == file["id"]


def test_unified_approval_download_without_direct_manager(people, monkeypatch):
    from apps.accounts.services.managers import set_managers
    from apps.weekly_report.services import submission_copy, submission_write

    owner, first, _, _ = people
    set_managers(owner.id, [])
    monkeypatch.setattr(
        reports,
        "get_template_by_code",
        lambda code, **kwargs: {"template_code": code, "tasks": [], "metrics": [], "fields": []},
    )
    file = upload(owner)
    part = {"role_code": "delivery", "payload": payload(file)}
    root = submission_write.save(
        owner, "delivery", "monthly", {"month_key": "2026-10", "parts": [part]}
    )
    submission_write.submit(owner, "delivery", int(root["plan"]["id"]))
    assert reports.get_report_attachment_for_download(
        user=first, role_code="manager", attachment_id=int(file["id"])
    ).id == int(file["id"])
    # Final copy uses a new record and file, including the aggregate copy path.
    from apps.weekly_report.submission_models import ReportSubmission

    ReportSubmission.objects.filter(id=root["plan"]["id"]).update(status="approved")
    MonthlyPlan.objects.filter(id=root["parts"][0]["id"]).update(status="approved")
    copied = submission_copy.copy(owner, "delivery", int(root["plan"]["id"]))
    assert copied["parts"][0]["payload"]["tasks"][0]["attachments"][0]["id"] != file["id"]


def test_failed_copy_rolls_back_files_and_rows(people, media):
    owner = people[0]
    set_monthly_approvers(owner.id, [])
    first, second = upload(owner, "first.txt"), upload(owner, "second.txt")
    value = payload(first)
    value["tasks"][0]["attachments"].append({"id": second["id"], "description": "缺失文件"})
    data = write.save(owner, "delivery", value)
    pid = int(data["plan"]["id"])
    write.submit(owner, "delivery", pid)
    default_storage.delete(Attachment.objects.get(id=second["id"]).storage_key)
    before = {str(path) for path in media.rglob("*") if path.is_file()}
    with pytest.raises(ValueError, match="文件不存在"):
        copy_next_month(owner, "delivery", pid)
    assert not MonthlyPlan.objects.filter(month_key="2026-11").exists()
    assert Attachment.objects.count() == 2
    assert {str(path) for path in media.rglob("*") if path.is_file()} == before
