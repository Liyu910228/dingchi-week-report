<script setup lang="ts">
import MonthlyPlanEvidenceCell from "./MonthlyPlanEvidenceCell.vue"
import { computed, ref } from "vue"
import { Plus } from "lucide-vue-next"
import type { DirectoryUserOption } from "@/features/directory/types"
import type { MonthlyPlanTask } from "@/features/weekly-report/monthly-plan/types"
import { emptyTask, type TaskFieldDefinition } from "@/features/weekly-report/task-draft"
import type { EditableTask } from "@/features/weekly-report/task-editing"
import TaskInlineField from "@/features/weekly-report/components/TaskInlineField.vue"
import TaskTextFieldDialog from "@/features/weekly-report/components/TaskTextFieldDialog.vue"
import { reportTaskStatusLabel } from "@/features/weekly-report/task-fields"
const props = defineProps<{ task: MonthlyPlanTask; fields: TaskFieldDefinition[]; readonly?: boolean; progressEditable?: boolean; contentSpan: number; users: DirectoryUserOption[] }>()
const emit = defineEmits<{ patch: [fields: Partial<MonthlyPlanTask>]; insertContent: [] }>()
const editing = ref<TaskFieldDefinition | null>(null)
const liveFields = new Set(["progress_text", "progress_percent", "quality_percent", "delay_reason", "on_time_status", "actual_completion_date", "owner_id", "owner_name", "collaborator_names", "document_links"])
function liveEditable(field: TaskFieldDefinition) {
  return Boolean(props.progressEditable && props.readonly && liveFields.has(field.code) && /^\d+$/.test(props.task.id))
}
function fieldReadonly(field: TaskFieldDefinition) {
  return Boolean(props.readonly && !liveEditable(field))
}
const textFields = ["work_content", "output_description", "progress_text", "delay_reason", "document_links"]
const draft = computed(() => ({ ...emptyTask(), ...props.task, client_key: props.task.id,
  task_name: props.task.work_task, customer_name: props.task.scope_name || "", work_content_group_key: props.task.content_group_key,
  work_content: props.task.work_content || "", output_description: props.task.output_description || "",
  planned_completion_date: props.task.planned_date || "",
}))
function patch(value: Partial<EditableTask>) {
  const { planned_completion_date, ...rest } = value
  emit("patch", { ...rest, ...("planned_completion_date" in value ? { planned_date: planned_completion_date || null } : {}) })
}
function display(field: TaskFieldDefinition) {
  const value = draft.value[field.code]
  if (field.code === "on_time_status") return reportTaskStatusLabel(String(value || ""))
  if (["progress_percent", "quality_percent", "completion_rate"].includes(field.code)) return `${value ?? 0}%`
  return String(value || "—")
}
</script>
<template>
  <template v-for="field in fields" :key="field.code">
    <td v-if="field.code !== 'work_content' || contentSpan" :rowspan="field.code === 'work_content' ? contentSpan : 1" :class="{ 'shared-cell': field.code === 'work_content' }">
      <MonthlyPlanEvidenceCell v-if="field.code === 'document_links' && !liveEditable(field)" :task="task" :readonly="fieldReadonly(field)" @patch="emit('patch',$event)" />
      <button v-else-if="!fieldReadonly(field) && textFields.includes(field.code)" class="text-cell user-content" type="button" :aria-label="`编辑${field.label}`" @click="editing = field">{{ draft[field.code] || `点击填写${field.label}` }}</button>
      <span v-else-if="fieldReadonly(field)" class="text-value" :class="{'user-content':field.code!=='on_time_status'}">{{ display(field) }}</span>
      <TaskInlineField v-else :task="draft" :field="field.code" :label="field.label" :users="users" @patch="patch" />
      <button data-task-tip="新增输出成果" aria-label="新增输出成果" v-if="field.code === 'work_content' && !readonly" class="cell-insert" type="button" @click="emit('insertContent')"><Plus :size="16" /></button>
    </td>
  </template>
  <TaskTextFieldDialog :open="Boolean(editing)" :title="editing?.label || ''" :value="editing ? String(draft[editing.code] || '') : ''" :max-length="10000" @close="editing = null" @save="value => { if (editing) patch({ [editing.code]: value }); editing = null }" />
</template>
<style scoped src="./MonthlyPlanTaskCells.css"></style>
