"""显式运维时间转换的数据访问；只处理 DATETIME，不处理 DATE/TIMESTAMP。"""

from django.apps import apps
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder


def tables():
    allowed = {model._meta.db_table for model in apps.get_models()}
    allowed.update({"django_migrations", "django_admin_log"})
    result = []
    with connection.cursor() as cursor:
        for table in sorted(allowed & set(connection.introspection.table_names(cursor))):
            description = connection.introspection.get_table_description(cursor, table)
            columns = [
                column.name
                for column in description
                if connection.introspection.get_field_type(column.type_code, column)
                == "DateTimeField"
            ]
            if columns:
                result.append((table, columns))
    return result


def was_converted():
    return MigrationRecorder.Migration.objects.filter(
        app="core", name="beijing_datetime_storage_v1"
    ).exists()


def mark_converted():
    MigrationRecorder(connection).record_applied("core", "beijing_datetime_storage_v1")


def acquire_lock():
    with connection.cursor() as cursor:
        cursor.execute("SELECT GET_LOCK(%s, %s)", ["dingchi_beijing_datetime_storage_v1", 0])
        return cursor.fetchone()[0] == 1


def release_lock():
    with connection.cursor() as cursor:
        cursor.execute("SELECT RELEASE_LOCK(%s)", ["dingchi_beijing_datetime_storage_v1"])


def snapshot_and_shift(table, columns):
    # 标识符仅来自 Django 模型及数据库 introspection，使用后端 quote_name，禁止用户传入。
    quote = connection.ops.quote_name
    with connection.cursor() as cursor:
        constraints = connection.introspection.get_constraints(cursor, table)
        keys = next(value["columns"] for value in constraints.values() if value["primary_key"])
        fields = ", ".join(map(quote, [*keys, *columns]))
        cursor.execute(f"SELECT {fields} FROM {quote(table)} FOR UPDATE")
        rows = cursor.fetchall()
        assignments = ", ".join(
            f"{quote(column)} = DATE_ADD({quote(column)}, INTERVAL 8 HOUR)" for column in columns
        )
        return [*keys, *columns], rows, f"UPDATE {quote(table)} SET {assignments}"


def shift(sql):
    with connection.cursor() as cursor:
        cursor.execute(sql)
        return cursor.rowcount
