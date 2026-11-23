import pytest

from apps.accounts.models import Role
from apps.weekly_report.models import ReportTemplate
from apps.weekly_report.services import reports

pytestmark = pytest.mark.django_db
MESSAGE = "模板未配置，不支持填写"


@pytest.mark.parametrize("code", ["", "  ", "nonexistent_template_v1"])
def test_missing_role_template_uses_unified_warning(code):
    Role.objects.create(role_code="test_position", role_name="测试职位", report_template_code=code)
    with pytest.raises(reports.ReportError) as error:
        reports.resolve_role_template("test_position")
    assert str(error.value) == MESSAGE


def test_inactive_template_uses_unified_warning():
    ReportTemplate.objects.create(
        template_code="delivery_specialist_v1", template_name="交付", status="inactive"
    )
    with pytest.raises(reports.ReportError) as error:
        reports.get_template_by_code("delivery_specialist_v1")
    assert str(error.value) == MESSAGE


def test_builtin_template_is_resolved_by_exact_code():
    template = reports.get_template_by_code("delivery_assistant_v1")
    assert template["template_code"] == "delivery_assistant_v1"


def test_unknown_code_never_returns_another_template():
    with pytest.raises(reports.ReportNotFoundError) as error:
        reports.get_template_by_code("unknown_v1")
    assert str(error.value) == MESSAGE
