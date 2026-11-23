import type { ObjectDirective } from "vue"
import { ColumnResizeController } from "@/shared/table/column-resize-controller"

const controllers = new WeakMap<HTMLTableElement, ColumnResizeController>()
export const vResizableColumns: ObjectDirective<HTMLTableElement, string> = {
  mounted(table, binding) { controllers.set(table, new ColumnResizeController(table, `mobile:${binding.value}`)) },
  updated(table, binding) { controllers.get(table)?.update(`mobile:${binding.value}`) },
  beforeUnmount(table) { controllers.get(table)?.destroy(); controllers.delete(table) },
}
