export interface ColumnLayout {
  header: HTMLTableCellElement
  key: string
  width: number
  left: boolean
  right: boolean
}

export function tableHeaders(table: HTMLTableElement): HTMLTableCellElement[] {
  return Array.from(table.tHead?.rows[0]?.cells || [])
}

/** 计算逻辑列号，兼容跨行合并，不依赖 tbody 的 cellIndex。 */
export function visitTableCells(table: HTMLTableElement, visit: (cell: HTMLTableCellElement, index: number) => void) {
  for (const section of [table.tHead, ...Array.from(table.tBodies)]) {
    const occupied: number[] = []
    for (const row of Array.from(section?.rows || [])) {
      let index = 0
      for (const cell of Array.from(row.cells)) {
        while ((occupied[index] || 0) > 0) index++
        if (cell.colSpan === 1) visit(cell, index)
        for (let offset = 0; offset < cell.colSpan; offset++) occupied[index + offset] = cell.rowSpan
        index += cell.colSpan
      }
      for (let offset = 0; offset < occupied.length; offset++) occupied[offset] = Math.max(0, (occupied[offset] || 0) - 1)
    }
  }
}

export function applyStickyOffsets(table: HTMLTableElement, columns: ColumnLayout[], remember: (element: HTMLElement) => void) {
  const total = columns.reduce((sum, column) => sum + column.width, 0)
  const lefts: number[] = []
  let offset = 0
  for (const column of columns) { lefts.push(offset); offset += column.width }
  visitTableCells(table, (cell, index) => {
    const column = columns[index]
    if (!column || (!column.left && !column.right)) return
    remember(cell)
    if (column.left) cell.style.left = `${lefts[index]}px`
    if (column.right) cell.style.right = `${total - (lefts[index] || 0) - column.width}px`
  })
}

export function applyColumnLayout(table: HTMLTableElement, columns: ColumnLayout[], remember: (element: HTMLElement) => void) {
  let group = table.querySelector<HTMLTableColElement>(":scope > colgroup[data-resize-managed]")
  if (!group) {
    group = document.createElement("colgroup")
    group.dataset.resizeManaged = "true"
    table.insertBefore(group, table.firstChild)
  }
  group.replaceChildren(...columns.map(column => {
    const col = document.createElement("col")
    col.style.width = `${column.width}px`
    remember(column.header)
    for (const property of ["width", "min-width", "max-width"]) column.header.style.setProperty(property, `${column.width}px`, "important")
    return col
  }))
  remember(table)
  table.style.setProperty("width", `${columns.reduce((sum, column) => sum + column.width, 0)}px`, "important")
  table.style.setProperty("min-width", "0", "important")
  applyStickyOffsets(table, columns, remember)
}
