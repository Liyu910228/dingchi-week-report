export type ColumnWidths = Record<string, number>
export const columnWidthEvent = "table-column-width-change"

export function columnWidthStorageKey(identity: string, fullscreen: boolean): string {
  return `table-column-widths:v1:${identity}:${fullscreen ? "fullscreen" : "normal"}`
}

export function readColumnWidths(key: string): ColumnWidths {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(key) || "{}")
    if (!value || typeof value !== "object" || Array.isArray(value)) return {}
    return Object.fromEntries(Object.entries(value).filter(([, width]) =>
      typeof width === "number" && Number.isFinite(width) && width >= 48 && width <= 10000,
    ))
  } catch { return {} }
}

/** 只保存用户操作的列，不把其他列的测量宽度写入存储。 */
export function saveColumnWidth(key: string, column: string, width: number): void {
  try {
    const widths = readColumnWidths(key)
    delete widths[column]
    localStorage.setItem(key, JSON.stringify({ ...widths, [column]: width }))
    window.dispatchEvent(new CustomEvent(columnWidthEvent, { detail: key }))
  } catch { /* 浏览器禁用存储时，本次拖动仍然有效。 */ }
}
