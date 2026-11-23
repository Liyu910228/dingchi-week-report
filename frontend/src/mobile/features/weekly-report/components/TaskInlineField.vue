<script setup lang="ts">
import { computed, nextTick, onMounted, onBeforeUnmount, ref } from "vue"
import PersonSelect from "@/mobile/features/directory/components/PersonSelect.vue"
import DeliveryCustomerSelect from "@/mobile/features/weekly-report/components/DeliveryCustomerSelect.vue"
import type { DirectoryUserOption } from "@/mobile/features/directory/types"
import type { EditableTaskColumn, EditableTask } from "@/mobile/features/weekly-report/task-editing"

const props = defineProps<{ task: EditableTask; field: EditableTaskColumn; label: string; users: DirectoryUserOption[] }>()
const emit = defineEmits<{ patch: [value: Partial<EditableTask>] }>()
const root = ref<HTMLElement | null>(null)
const menuStyle = ref<Record<string, string>>({})
const displayText = computed(() => {
  if (["progress_percent", "quality_percent", "completion_rate"].includes(props.field)) return `${props.task[props.field] ?? 0}%`
  if (props.field === "on_time_status") {
    const labels: Record<string, string> = { pending: "待完成", in_progress: "进行中", on_time: "按时完成", late: "延期完成", overdue: "逾期未完成", completed: "已完成", not_applicable: "不适用" }
    return labels[props.task.on_time_status] || "—"
  }
  if (props.field === "owner_name") return props.task.owner_name || props.users.find(user => user.id === props.task.owner_id)?.display_name || "—"
  return String(props.task[props.field] || "—")
})
const owner = computed(() => props.task.owner_id || props.users.find(user => user.display_name === props.task.owner_name)?.id || "")
const collaboratorNames = computed(() => props.task.collaborator_names.split(/[、,，]/).map(name => name.trim()).filter(Boolean))
const collaborators = computed(() => props.users.filter(user => collaboratorNames.value.includes(user.display_name)).map(user => user.id))
function setOwner(value: string | string[]) {
  const id = String(value || "")
  emit("patch", { owner_id: id || null, owner_name: props.users.find(user => user.id === id)?.display_name || "" })
}
function setCollaborators(value: string | string[]) {
  const ids = Array.isArray(value) ? value : value ? [value] : []
  const unknown = collaboratorNames.value.filter(name => !props.users.some(user => user.display_name === name))
  emit("patch", { collaborator_names: [...unknown, ...props.users.filter(user => ids.includes(user.id)).map(user => user.display_name)].join("、") })
}
function normalizeNumberInput(event: Event) {
  const input = event.target as HTMLInputElement
  const normalized = input.value.replace(/^(-?)0+(?=\d)/, "$1")
  if (normalized !== input.value) input.value = normalized
}
function change(event: Event) {
  const input = event.target as HTMLInputElement
  const value = input.value
  if (props.field === "progress_percent" || props.field === "quality_percent") {
    const number = Number(value)
    const normalized = Number.isFinite(number) ? Math.min(100, Math.max(0, Math.round(number / 5) * 5)) : 0
    input.value = String(normalized)
    emit("patch", { [props.field]: normalized })
  } else emit("patch", { [props.field]: value })
}
async function positionMenu() {
  await nextTick()
  const menu = root.value?.querySelector<HTMLElement>(".searchable-select__menu")
  if (!menu) return
  const rect = root.value?.getBoundingClientRect()
  if (!rect) return
  const width = Math.min(menu.getBoundingClientRect().width || rect.width, window.innerWidth - 24)
  const below = window.innerHeight - rect.bottom - 16
  const above = below < 180 && rect.top > below
  const height = Math.max(80, Math.min(320, above ? rect.top - 20 : below))
  const renderedHeight = Math.min(height, menu.scrollHeight)
  menuStyle.value = {
    "--cell-menu-left": `${Math.max(12, Math.min(rect.left, window.innerWidth - width - 12))}px`,
    "--cell-menu-top": `${above ? Math.max(12, rect.top - renderedHeight - 4) : rect.bottom + 4}px`,
    "--cell-menu-height": `${height}px`,
    "--cell-control-width": `${Math.min(rect.width, window.innerWidth - 24)}px`,
  }
}
onMounted(() => { window.addEventListener("scroll", positionMenu, true); window.addEventListener("resize", positionMenu) })
onBeforeUnmount(() => { window.removeEventListener("scroll", positionMenu, true); window.removeEventListener("resize", positionMenu) })
</script>
<template>
  <div ref="root" class="inline-field" :class="{ 'inline-field--readonly': field === 'completion_rate' }" :style="menuStyle" tabindex="0" :aria-label="`${label}：${displayText}`" @pointerdown.capture="positionMenu" @focusin.capture="positionMenu" @input.capture="positionMenu">
    <span class="inline-field__text" :class="{'user-content':field!=='on_time_status'}">{{ displayText }}</span>
    <div v-if="field !== 'completion_rate'" class="inline-field__editor">
    <DeliveryCustomerSelect v-if="field === 'customer_name'" :model-value="task.customer_name || ''" required teleport-menu @update:model-value="emit('patch', { customer_name: $event })" />
    <PersonSelect v-else-if="field === 'owner_name'" :model-value="owner" :users="users" :aria-label="label" placeholder="选择责任人" @update:model-value="setOwner" />
    <PersonSelect v-else-if="field === 'collaborator_names'" :model-value="collaborators" :users="users" multiple :aria-label="label" placeholder="选择协作人" @update:model-value="setCollaborators" />
    <select v-else-if="field === 'on_time_status'" :value="task.on_time_status" :aria-label="label" @change="change">
      <option value="pending">待完成</option><option value="in_progress">进行中</option><option value="on_time">是，按计划完成</option><option value="late">否，已延期完成</option><option value="overdue">否，已逾期未完成</option><option value="completed">已完成</option><option value="not_applicable">不适用</option>
    </select>
    <input class="user-content" v-else-if="field === 'progress_percent' || field === 'quality_percent'" :value="task[field] ?? 0" type="number" min="0" max="100" step="5" :aria-label="label" @input="normalizeNumberInput" @change="change" />
    <input class="user-content" v-else-if="field === 'planned_completion_date' || field === 'actual_completion_date'" :value="task[field]" type="date" :aria-label="label" @change="change" />
    <input class="user-content" v-else :maxlength="field === 'dimension' ? 64 : undefined" :value="task[field]" :aria-label="label" @change="change" />
    </div>
  </div>
</template>
<style scoped src="./TaskInlineField.css"></style>
