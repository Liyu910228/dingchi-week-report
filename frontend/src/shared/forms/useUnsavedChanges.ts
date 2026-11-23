import { computed, ref, watch } from "vue"

/** 比较可编辑数据与上次加载/保存的快照，改回原值后不再提示。 */
export function useUnsavedChanges(source: () => unknown, ready: () => boolean) {
  const baseline = ref<string | null>(null)
  const resetKey = ref(0)
  function snapshot() { return JSON.stringify(source()) }
  function markSaved(value = snapshot()) {
    baseline.value = value
    resetKey.value += 1
  }
  watch(ready, (loaded) => {
    if (loaded && baseline.value === null) markSaved()
  }, { immediate: true, flush: "sync" })
  const hasChanges = computed(() => ready() && baseline.value !== null && snapshot() !== baseline.value)
  return { hasChanges, resetKey, snapshot, markSaved }
}
