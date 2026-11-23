<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue"
import { onBeforeRouteLeave, onBeforeRouteUpdate } from "vue-router"
import ConfirmDialog from "@/components/feedback/ConfirmDialog.vue"

const props = defineProps<{ dirty: boolean; enabled: boolean; resetKey: number }>()
const open = ref(false)
const confirmationAction = ref<"leave" | "refresh">("leave")
const drafts = new Map<HTMLFormElement, { initial: string; edited: boolean }>()
let observer: MutationObserver | null = null
let resolveLeave: ((leave: boolean) => void) | null = null
let refreshConfirmationPending = false
let skipNextBeforeUnload = false

function formSnapshot(form: HTMLFormElement) {
  const fields = [...form.querySelectorAll<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>("input,textarea,select")]
    .map(field => field instanceof HTMLInputElement && ["checkbox", "radio"].includes(field.type) ? field.checked : field.value)
  const selections = [...form.querySelectorAll(".searchable-select__chip,.searchable-select__selected")].map(item => item.textContent)
  return JSON.stringify([fields, selections])
}

function scanDialogs() {
  for (const form of drafts.keys()) if (!form.isConnected) drafts.delete(form)
  for (const form of document.querySelectorAll<HTMLFormElement>('[role="dialog"] form')) {
    const draft = drafts.get(form)
    if (!draft?.edited) drafts.set(form, { initial: formSnapshot(form), edited: false })
  }
}

function trackInput(event: Event) {
  // 自定义人员/客户选择器通过点击按钮改变值。
  if (event.type === "click" && !(event.target instanceof Element && event.target.closest('[role="option"],.searchable-select__chip button,.searchable-select__clear'))) return
  const form = event.target instanceof Element ? event.target.closest<HTMLFormElement>('[role="dialog"] form') : null
  const draft = form ? drafts.get(form) : null
  if (draft) draft.edited = true
}

function hasChanges() {
  if (!props.enabled) return false
  return props.dirty || [...drafts].some(([form, draft]) => draft.edited && form.isConnected && formSnapshot(form) !== draft.initial)
}

function finish(leave: boolean) {
  open.value = false
  const resolve = resolveLeave
  resolveLeave = null
  resolve?.(leave)
}

function requestConfirmation(action: "leave" | "refresh") {
  if (!hasChanges()) return true
  if (resolveLeave) return false
  confirmationAction.value = action
  open.value = true
  return new Promise<boolean>(resolve => { resolveLeave = resolve })
}

function confirmLeave() {
  return requestConfirmation("leave")
}

async function handleRefreshKey(event: KeyboardEvent) {
  if (event.key !== "F5" || event.ctrlKey || event.metaKey || event.altKey || event.shiftKey) return
  if (!event.cancelable || !hasChanges()) return
  event.preventDefault()
  event.stopPropagation()
  if (event.repeat || refreshConfirmationPending) return
  refreshConfirmationPending = true
  try {
    if (!await requestConfirmation("refresh")) return
    // 用户已在自定义弹窗确认，仅放行这一次刷新，避免再次弹出原生提示。
    skipNextBeforeUnload = true
    window.location.reload()
  } catch {
    skipNextBeforeUnload = false
  } finally {
    refreshConfirmationPending = false
  }
}

function beforeUnload(event: BeforeUnloadEvent) {
  if (skipNextBeforeUnload) { skipNextBeforeUnload = false; return }
  if (!hasChanges()) return
  event.preventDefault()
  event.returnValue = ""
}

onBeforeRouteLeave(confirmLeave)
onBeforeRouteUpdate((to, from) => to.path === from.path ? true : confirmLeave())
watch(() => props.resetKey, () => {
  drafts.clear()
  scanDialogs()
})
onMounted(() => {
  window.addEventListener("beforeunload", beforeUnload)
  window.addEventListener("keydown", handleRefreshKey, true)
  document.addEventListener("focusin", scanDialogs, true)
  document.addEventListener("input", trackInput, true)
  document.addEventListener("change", trackInput, true)
  document.addEventListener("click", trackInput, true)
  observer = new MutationObserver(scanDialogs)
  observer.observe(document.body, { childList: true, subtree: true })
  scanDialogs()
})
onUnmounted(() => {
  window.removeEventListener("beforeunload", beforeUnload)
  window.removeEventListener("keydown", handleRefreshKey, true)
  document.removeEventListener("focusin", scanDialogs, true)
  document.removeEventListener("input", trackInput, true)
  document.removeEventListener("change", trackInput, true)
  document.removeEventListener("click", trackInput, true)
  observer?.disconnect()
  drafts.clear()
  finish(false)
})
</script>

<template>
  <ConfirmDialog :open="open" title="有未保存的内容" :message="confirmationAction === 'refresh' ? '当前填写内容尚未保存，刷新后将丢失。确定刷新吗？' : '当前填写内容尚未保存，离开后将丢失。确定离开吗？'" confirm-label="确定" @close="finish(false)" @confirm="finish(true)" />
</template>
