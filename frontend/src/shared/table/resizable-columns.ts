import type { ObjectDirective } from "vue"
import { ColumnResizeController } from "./column-resize-controller"

const controllers = new WeakMap<HTMLTableElement, ColumnResizeController>()
export const vResizableColumns: ObjectDirective<HTMLTableElement, string> = {
  mounted(table, binding) { controllers.set(table, new ColumnResizeController(table, binding.value)) },
  updated(table, binding) { controllers.get(table)?.update(binding.value) },
  beforeUnmount(table) { controllers.get(table)?.destroy(); controllers.delete(table) },
}
