import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


@pytest.mark.django_db(transaction=True)
def test_scope_merge_preserves_customer_and_dimension_records():
    before = [("weekly_report", "0006_monthly_plan_scope_nullable")]
    after = [("weekly_report", "0011_restore_effective_monthly_plans")]
    executor = MigrationExecutor(connection)
    executor.migrate(before)
    try:
        model = executor.loader.project_state(before).apps.get_model(
            "weekly_report", "MonthlyPlanTask"
        )
        customer = model.objects.create(
            employee_id=101,
            role_code="delivery_specialist",
            month_key="2026-10",
            customer_name="原客户",
            dimension=None,
            work_task="交付计划",
        )
        dimension = model.objects.create(
            employee_id=101,
            role_code="recruitment",
            month_key="2026-10",
            customer_name=None,
            dimension="总体目标",
            work_task="招聘计划",
        )
        empty = model.objects.create(
            employee_id=101,
            role_code="functional_group",
            month_key="2026-10",
            customer_name=None,
            dimension=None,
            work_task="职能计划",
        )
        executor = MigrationExecutor(connection)
        executor.migrate(after)
        model = executor.loader.project_state(after).apps.get_model(
            "weekly_report", "MonthlyPlanTask"
        )
        assert model.objects.get(id=customer.id).scope_name == "原客户"
        assert model.objects.get(id=dimension.id).scope_name == "总体目标"
        assert model.objects.get(id=empty.id).scope_name is None
        assert list(model.objects.order_by("role_code").values_list("work_task", flat=True)) == [
            "交付计划",
            "职能计划",
            "招聘计划",
        ]
        with connection.cursor() as cursor:
            fields = connection.introspection.get_table_description(cursor, "monthly_plan_task")
        scope_columns = [
            field
            for field in fields
            if field.name
            in {
                "scope_name",
                "customer_name",
                "dimension",
            }
        ]
        assert len(scope_columns) == 1
        assert scope_columns[0].name == "scope_name" and scope_columns[0].null_ok
    finally:
        MigrationExecutor(connection).migrate(after)
