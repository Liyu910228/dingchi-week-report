/** 业务时间统一按北京时间展示；带时区时间转换，无时区历史文本保留原值。 */
const businessDateTime = new Intl.DateTimeFormat("en-CA", {
  timeZone: "Asia/Shanghai",
  year: "numeric", month: "2-digit", day: "2-digit",
  hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23",
})

export function formatDateTime(
  value: string | Date | null | undefined,
  empty = "—",
): string {
  if (value === null || value === undefined || value === "") return empty
  const source = value instanceof Date ? "" : String(value)
  // DATE 和历史无时区文本不代表 UTC 时刻，避免把周报周期或业务日期移到另一日。
  const isInstant = value instanceof Date || /(?:Z|[+-]\d{2}:?\d{2})$/i.test(source)
  if (isInstant) {
    const date = value instanceof Date ? value : new Date(source)
    if (Number.isNaN(date.getTime())) return source || empty
    const parts = Object.fromEntries(businessDateTime.formatToParts(date).map(part => [part.type, part.value]))
    return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}:${parts.second}`
  }
  const match = source.match(/^(\d{4}-\d{2}-\d{2})(?:[T ](\d{2}:\d{2}:\d{2}))?/)
  if (!match) return source
  return match[1] + " " + (match[2] || "00:00:00")
}

/** 显示周报周期的日期范围，不带时区和 ISO 分隔符。 */
export function formatPeriod(
  periodStart: string | null | undefined,
  periodEnd: string | null | undefined,
): string {
  const start = formatDateTime(periodStart, "")
  const end = formatDateTime(periodEnd, "")
  if (!start && !end) return "未设置周期"
  if (!end) return start.slice(0, 10)
  return start.slice(0, 10) + " 至 " + end.slice(0, 10)
}
