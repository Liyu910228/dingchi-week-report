import type { ObjectDirective } from "vue"
import { rowBands } from "./row-bands"

interface Controller { refresh: () => void; destroy: () => void }
const controllers = new WeakMap<HTMLTableElement, Controller>()

function mount(table: HTMLTableElement): Controller {
  table.dataset.rowBanded = "true"
  let frame = 0
  function apply() {
    for (const body of table.tBodies) {
      const rows = [...body.rows]
      const bands = rowBands(rows.map(row => ({
        spans: [...row.cells].map(cell => cell.rowSpan),
        kind: row.dataset.rowKind === "change" ? "change" as const :
          [...row.cells].some(cell => [...cell.classList].some(name => name.includes("empty"))) ? "empty" as const : undefined,
      })))
      rows.forEach((row, index) => {
        row.dataset.rowBand = bands[index]
        const state = row.dataset.rowState || "draft"
        row.style.setProperty("--current-row-background", bands[index] === "change"
          ? `var(--row-change-${["draft", "pending", "approved", "rejected"].includes(state) ? state : "draft"})`
          : `var(--row-${bands[index] === "alternate" ? "alternate" : "base"})`)
      })
    }
  }
  function refresh() {
    cancelAnimationFrame(frame)
    frame = requestAnimationFrame(apply)
  }
  const observer = new MutationObserver(refresh)
  observer.observe(table, { childList: true, subtree: true, attributes: true,
    attributeFilter: ["rowspan", "data-row-kind", "data-row-state"] })
  apply()
  return { refresh, destroy() { observer.disconnect(); cancelAnimationFrame(frame) } }
}

/** 表头不着色，tbody按合并组着色；异步加载、分页和展开子变更后自动重算。 */
export const vRowBackgrounds: ObjectDirective<HTMLTableElement> = {
  mounted(table) { controllers.set(table, mount(table)) },
  updated(table) { controllers.get(table)?.refresh() },
  beforeUnmount(table) { controllers.get(table)?.destroy(); controllers.delete(table) },
}
