import type { ColumnLayout } from "./column-width-layout"

/** 在固定表宽内分配剩余空间；先调整未手动设置的列，空间不足时才收缩已设置列。 */
export function fitColumnWidths(columns: ColumnLayout[], total: number, saved: Set<string>, active?: string) {
  let remaining = total - columns.reduce((sum, column) => sum + column.width, 0)
  const candidates = [...columns].sort((a, b) => {
    const rank = (column: ColumnLayout) => column.key === active ? 3 : saved.has(column.key) ? 2 : column.key === "work_content" ? 0 : 1
    const origin = columns.findIndex(column => column.key === active)
    const ai = columns.indexOf(a), bi = columns.indexOf(b)
    return rank(a) - rank(b) || Math.abs(ai - origin) - Math.abs(bi - origin) || bi - ai
  })
  if (remaining > 0 && candidates[0]) candidates[0].width += remaining
  else for (const column of candidates) {
    const change = Math.min(-remaining, Math.max(0, column.width - 48))
    column.width -= change
    remaining += change
    if (remaining >= -0.01) break
  }
}
