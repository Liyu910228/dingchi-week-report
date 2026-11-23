import { computed } from "vue"
import { useAuthStore } from "./store"

/** 列表列宽按账号、列表和视图隔离；仅实际拖动的列由公共控制器持久化。 */
export function useUserTableResizeKey(list: () => string) {
  const auth = useAuthStore()
  return computed(() => `${auth.user?.id || "anonymous"}:lists:${list()}`)
}
