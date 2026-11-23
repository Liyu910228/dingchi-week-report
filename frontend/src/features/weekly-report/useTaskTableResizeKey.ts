import { computed } from "vue"
import { useAuthStore } from "@/features/auth/store"

/** 查看/编辑共用同一字段宽度；模板、列表类型、用户分别隔离，显示模式由表格控制器追加。 */
export function useTaskTableResizeKey(kind: "monthly" | "weekly" | "daily", template: () => string | undefined) {
  const auth = useAuthStore()
  return computed(() => `${auth.user?.id || "anonymous"}:${template() || "default"}:${kind}`)
}
