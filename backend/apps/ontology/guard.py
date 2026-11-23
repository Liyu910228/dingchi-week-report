"""text-to-SQL 权限护栏：AI 的数据权限 = 当前登录用户本人的数据权限。

设计要点：
- 护栏包装在传给 text-to-SQL agent 的 connector 上，agent 内部所有 SQL
  执行（探查、验证、取数）都会被改写，避免"结果行过滤了但回答文本已泄露"。
- 员工维度表在【表读取层】被替换为带 employee_id 过滤的子查询，
  因此聚合（COUNT/GROUP BY）也天然只统计权限范围内的数据。
- 只读：仅允许单条 SELECT/WITH 查询，禁止任何写操作节点。
- 限量：无 LIMIT 的查询自动补 LIMIT，防止全表扫描撑爆上下文。
"""

from __future__ import annotations

import sqlglot
from sqlglot import exp

MAX_ROWS = 200

# 员工维度表 -> 过滤列（按当前用户可见 employee_id 集合过滤）
_EMPLOYEE_COLUMN = {
    "weekly_report": "employee_id",
    "monthly_plan": "employee_id",
    "monthly_plan_task": "employee_id",
    "user_account": "id",
}

# 周报条目表没有 employee_id，经 report_id 关联周报主表过滤
_ITEM_TABLE = "weekly_report_item"


class SqlGuardError(ValueError):
    """SQL 未通过安全校验。"""


def guard_sql(
    sql: str, visible_ids: list[int] | None, max_rows: int = MAX_ROWS
) -> str:
    """校验并改写 SQL。visible_ids=None 表示全部可见（all scope），否则为可见员工 ID 集合。"""
    try:
        statements = [s for s in sqlglot.parse(sql, dialect="mysql") if s is not None]
    except Exception as exc:
        raise SqlGuardError(f"SQL 解析失败：{exc}") from exc
    if len(statements) != 1:
        raise SqlGuardError("只允许单条查询语句。")
    stmt = statements[0]
    if not isinstance(stmt, exp.Query):
        raise SqlGuardError("只允许 SELECT 查询。")
    # 双保险：遍历全部节点，禁止任何写操作/DDL
    for node in stmt.walk():
        if isinstance(
            node,
            (
                exp.Insert,
                exp.Update,
                exp.Delete,
                exp.Create,
                exp.Drop,
                exp.Alter,
                exp.Command,
            ),
        ):
            raise SqlGuardError("检测到非只读操作，已拒绝执行。")

    if visible_ids is not None:
        _inject_employee_scope(stmt, visible_ids)

    if stmt.args.get("limit") is None:
        stmt = stmt.limit(max_rows)
    return stmt.sql(dialect="mysql")


def _inject_employee_scope(stmt: exp.Expression, visible_ids: list[int]) -> None:
    """把员工维度表替换为过滤子查询；空集合用永假条件。"""
    ids = ",".join(str(int(i)) for i in visible_ids) if visible_ids else "-1"
    # 先收集再替换：注入子查询内部的新表节点不会被二次处理
    tables = list(stmt.find_all(exp.Table))
    for table in tables:
        name = (table.name or "").lower()
        if not name:
            continue
        full = f"{table.db}.{name}" if table.db else name
        if name in _EMPLOYEE_COLUMN:
            col = _EMPLOYEE_COLUMN[name]
            sub_sql = f"(SELECT * FROM {full} WHERE {col} IN ({ids}))"
        elif name == _ITEM_TABLE:
            sub_sql = (
                f"(SELECT * FROM {full} WHERE report_id IN "
                f"(SELECT id FROM weekly_report WHERE employee_id IN ({ids})))"
            )
        else:
            continue
        sub = sqlglot.parse_one(sub_sql, dialect="mysql")
        # 保留原别名；无别名时以原表名作为子查询别名，保证外层引用可解析
        alias = table.alias or name
        sub.set("alias", exp.TableAlias(this=exp.to_identifier(alias)))
        table.replace(sub)


class GuardedConnector:
    """包装 auto_ontology connector：execute 前注入当前用户数据权限。

    其余方法（schema 内省等）通过 __getattr__ 原样转发。
    """

    def __init__(self, inner, visible_ids: list[int] | None) -> None:
        self._inner = inner
        self._visible_ids = visible_ids

    @property
    def dialect(self):
        return self._inner.dialect

    @property
    def database_name(self):
        return self._inner.database_name

    def execute(self, sql: str, parameters=None, **kwargs):
        safe_sql = guard_sql(sql, self._visible_ids)
        return self._inner.execute(safe_sql, parameters, **kwargs)

    def __getattr__(self, name):
        return getattr(self._inner, name)
