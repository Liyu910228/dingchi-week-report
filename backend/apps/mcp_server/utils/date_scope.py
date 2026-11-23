"""周报周期（年/月/周/日）到数据库查询条件的转换。

规则（与系统一致）：一周为周一~周日；跨月的周归属于「周一所在月份」。
因此 monthly_key 取自周期开始日（周一）的月份。
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def first_monday_on_or_after(y: int, m: int) -> date:
    """返回 y 年 m 月 1 日当天或之后的第一个周一。"""
    d = date(y, m, 1)
    while d.weekday() != 0:  # Monday == 0
        d += timedelta(days=1)
    return d


def monday_of(d: date) -> date:
    """返回 d 所在周的周一。"""
    return d - timedelta(days=d.weekday())


def week_index_of_month(d: date) -> int:
    """d 所在周是该月的第几周（按周一归属月规则，1 基）。"""
    fm = first_monday_on_or_after(d.year, d.month)
    return (d - fm).days // 7 + 1


def month_key_of(d: date) -> str:
    return d.strftime("%Y-%m")


def parse_date(text: str | None) -> date | None:
    text = (text or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return date.strptime(text, fmt)
        except ValueError:
            continue
    return None


def resolve_period(
    *,
    year: int | None = None,
    month: int | None = None,
    week: int | None = None,
    day: str | None = None,
) -> dict[str, Any]:
    """将解析出的参数归一成查询条件。

    优先级：day > week > month > 默认(本周)。
      - 啥都没给：今年本月本周。
      - 只给 month：整月（用 month_key 过滤）。
      - 给 week（可带 month，缺省当月）：该周（用 period_start/period_end 过滤）。
      - 给 day：该日所在周。
    """
    today = date.today()
    y = int(year) if year else today.year
    m = int(month) if month else today.month

    target_date = parse_date(day)
    if target_date is not None:
        start = monday_of(target_date)
        end = start + timedelta(days=6)
        return {
            "mode": "day",
            "year": start.year,
            "month": start.month,
            "week": week_index_of_month(start),
            "target_date": target_date.isoformat(),
            "month_key": month_key_of(start),
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
        }

    if week is not None:
        w = int(week)
        start = first_monday_on_or_after(y, m) + timedelta(days=7 * (w - 1))
        end = start + timedelta(days=6)
        return {
            "mode": "week",
            "year": y,
            "month": m,
            "week": w,
            "target_date": None,
            "month_key": month_key_of(start),
            "period_start": start.isoformat(),
            "period_end": end.isoformat(),
        }

    if month is not None:
        return {
            "mode": "month",
            "year": y,
            "month": m,
            "week": None,
            "target_date": None,
            "month_key": f"{y:04d}-{m:02d}",
            "period_start": None,
            "period_end": None,
        }

    # 默认：本周
    start = monday_of(today)
    end = start + timedelta(days=6)
    return {
        "mode": "week",
        "year": start.year,
        "month": start.month,
        "week": week_index_of_month(start),
        "target_date": None,
        "month_key": month_key_of(start),
        "period_start": start.isoformat(),
        "period_end": end.isoformat(),
    }
