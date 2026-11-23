import { applyColumnLayout, applyStickyOffsets, tableHeaders, type ColumnLayout } from "./column-width-layout"
import { columnWidthEvent, columnWidthStorageKey, readColumnWidths, saveColumnWidth } from "./column-width-storage"
import { fitColumnWidths } from "./fit-column-widths"

export class ColumnResizeController {
  private identity: string
  private panel: Element | null
  private columns: ColumnLayout[] = []
  private original = new Map<HTMLElement, string | null>()
  private lifetime = new AbortController()
  private drag: AbortController | null = null
  private handlesLifetime = new AbortController()
  private observer: MutationObserver
  private sizeObserver: ResizeObserver
  private frame = 0
  private signature = ""
  private containerWidth = 0
  private fitWidth = 0

  constructor(private table: HTMLTableElement, identity: string) {
    this.identity = identity
    this.panel = table.closest(".fullscreen-panel")
    table.dataset.resizableColumns = "true"
    this.observer = new MutationObserver(records => {
      if (records.some(record => record.type === "attributes" || !this.managedMutation(record))) this.schedule()
    })
    this.observer.observe(table, { childList: true, subtree: true })
    if (this.panel) this.observer.observe(this.panel, { attributes: true, attributeFilter: ["class"] })
    this.sizeObserver = new ResizeObserver(() => {
      const width = table.parentElement?.clientWidth || 0
      if (width !== this.containerWidth) { this.containerWidth = width; this.signature = ""; this.schedule() }
    })
    if (table.parentElement) this.sizeObserver.observe(table.parentElement)
    const options = { signal: this.lifetime.signal }
    window.addEventListener("storage", () => { this.signature = ""; this.schedule() }, options)
    window.addEventListener(columnWidthEvent, () => { this.signature = ""; this.schedule() }, options)
    this.refresh()
  }

  private key() { return columnWidthStorageKey(this.identity, Boolean(this.panel?.classList.contains("fullscreen-panel--expanded"))) }
  private managedMutation(record: MutationRecord) {
    return [...record.addedNodes, ...record.removedNodes].every(node => node instanceof HTMLElement
      && (node.classList.contains("column-resize-handle") || node.matches("col, colgroup[data-resize-managed]")))
  }
  private remember = (element: HTMLElement) => {
    if (!this.original.has(element)) this.original.set(element, element.getAttribute("style"))
  }
  private resetLayout() {
    this.table.querySelector(":scope > colgroup[data-resize-managed]")?.remove()
    for (const [element, style] of this.original) {
      if (style === null) element.removeAttribute("style")
      else element.setAttribute("style", style)
    }
    this.original.clear()
  }
  private schedule() {
    if (!this.frame) this.frame = requestAnimationFrame(() => { this.frame = 0; if (!this.drag) this.refresh() })
  }
  update(identity: string) {
    this.identity = identity
    const original = this.original.get(this.table)
    // Vue更新动态字段时可能同步修改默认min-width，重测时使用新默认值。
    if (original !== undefined && this.table.style.minWidth !== "0px") {
      const baseline = document.createElement("table")
      baseline.style.cssText = original || ""
      baseline.style.minWidth = this.table.style.minWidth
      this.original.set(this.table, baseline.getAttribute("style"))
    }
    this.schedule()
  }

  private refresh() {
    const headers = tableHeaders(this.table)
    const signature = `${this.key()}:${headers.map(header => header.dataset.columnKey).join("|")}`
    if (signature === this.signature) {
      // 业务组件重渲染会重新写入默认min-width，不能让它撑大用户缩窄后的列。
      if (this.table.querySelector(":scope > colgroup[data-resize-managed]") && this.table.style.minWidth !== "0px") {
        applyColumnLayout(this.table, this.columns, this.remember)
      } else applyStickyOffsets(this.table, this.columns, this.remember)
      return
    }
    this.signature = signature
    const focusedKey = document.activeElement?.classList.contains("column-resize-handle")
      ? document.activeElement.closest<HTMLTableCellElement>("th")?.dataset.columnKey : undefined
    this.handlesLifetime.abort(); this.handlesLifetime = new AbortController()
    this.table.querySelectorAll(".column-resize-handle").forEach(handle => handle.remove())
    this.resetLayout()
    this.fitWidth = this.table.dataset.resizeFit === "true" ? this.table.getBoundingClientRect().width : 0
    this.columns = headers.map(header => {
      const style = getComputedStyle(header)
      return { header, key: header.dataset.columnKey || "", width: header.getBoundingClientRect().width,
        left: style.position === "sticky" && style.left !== "auto", right: style.position === "sticky" && style.right !== "auto" }
    })
    const saved = readColumnWidths(this.key())
    if (this.columns.some(column => column.key in saved)) {
      this.columns.forEach(column => { column.width = saved[column.key] || column.width })
      if (this.fitWidth) fitColumnWidths(this.columns, this.fitWidth, new Set(Object.keys(saved)), Object.keys(saved).at(-1))
      applyColumnLayout(this.table, this.columns, this.remember)
    }
    for (const column of this.columns) this.addHandle(column)
    if (focusedKey) this.columns.find(column => column.key === focusedKey)?.header
      .querySelector<HTMLElement>(".column-resize-handle")?.focus({ preventScroll: true })
  }

  private addHandle(column: ColumnLayout) {
    if (!column.key || column.header.querySelector(".column-resize-handle")) return
    const handle = document.createElement("span")
    handle.className = "column-resize-handle"
    handle.tabIndex = 0
    handle.setAttribute("role", "separator")
    handle.setAttribute("aria-orientation", "vertical")
    handle.setAttribute("aria-label", `调整${column.header.textContent?.trim()}列宽`)
    this.remember(column.header)
    if (getComputedStyle(column.header).position === "static") column.header.style.position = "relative"
    handle.addEventListener("pointerdown", event => this.startDrag(event, column), { signal: this.handlesLifetime.signal })
    handle.addEventListener("keydown", event => this.keyboardResize(event, column), { signal: this.handlesLifetime.signal })
    column.header.append(handle)
  }

  private startDrag(event: PointerEvent, column: ColumnLayout) {
    if (event.button !== 0) return
    event.preventDefault(); event.stopPropagation()
    const start = event.clientX, width = column.header.getBoundingClientRect().width
    const key = this.key()
    const baseline = this.columns.map(item => item.width)
    this.drag?.abort()
    this.drag = new AbortController()
    const signal = this.drag.signal
    this.table.classList.add("is-resizing-columns")
    document.documentElement.classList.add("is-resizing-table-columns")
    const move = (next: PointerEvent) => {
      if (next.pointerId !== event.pointerId) return
      this.columns.forEach((item, index) => { item.width = baseline[index]! })
      column.width = Math.max(48, Math.min(10000, Math.round(width + next.clientX - start)))
      if (this.fitWidth) fitColumnWidths(this.columns, this.fitWidth, new Set(Object.keys(readColumnWidths(key))), column.key)
      applyColumnLayout(this.table, this.columns, this.remember)
    }
    window.addEventListener("pointermove", move, { signal })
    window.addEventListener("pointerup", next => {
      if (next.pointerId !== event.pointerId) return
      if (Math.abs(next.clientX - start) >= 2 && key === this.key()) {
        move(next); saveColumnWidth(key, column.key, column.width)
      }
      this.endDrag()
    }, { signal })
    window.addEventListener("pointercancel", () => this.endDrag(), { signal })
    window.addEventListener("blur", () => this.endDrag(), { signal })
  }
  private endDrag() {
    this.drag?.abort(); this.drag = null
    this.table.classList.remove("is-resizing-columns")
    document.documentElement.classList.remove("is-resizing-table-columns")
    this.signature = ""; this.schedule()
  }
  private keyboardResize(event: KeyboardEvent, column: ColumnLayout) {
    if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return
    event.preventDefault(); event.stopPropagation()
    column.width = Math.max(48, Math.min(10000, Math.round(column.header.getBoundingClientRect().width + (event.key === "ArrowRight" ? 10 : -10))))
    if (this.fitWidth) fitColumnWidths(this.columns, this.fitWidth, new Set(Object.keys(readColumnWidths(this.key()))), column.key)
    applyColumnLayout(this.table, this.columns, this.remember)
    saveColumnWidth(this.key(), column.key, column.width)
  }
  destroy() {
    if (this.drag) this.endDrag()
    this.drag?.abort(); this.handlesLifetime.abort(); this.lifetime.abort(); this.observer.disconnect(); this.sizeObserver.disconnect()
    cancelAnimationFrame(this.frame)
    this.table.querySelectorAll(".column-resize-handle").forEach(handle => handle.remove())
    this.resetLayout(); delete this.table.dataset.resizableColumns
  }
}
