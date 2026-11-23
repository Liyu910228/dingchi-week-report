<script setup lang="ts" generic="T extends EditableTask">
import { vResizableColumns } from "@/shared/table/resizable-columns"
import { useTaskTableResizeKey } from "@/features/weekly-report/useTaskTableResizeKey"
import { computed, ref } from "vue"
import { Plus } from "lucide-vue-next"
import type { DirectoryUserOption } from "@/features/directory/types"
import type { EditableTask, EditableTaskColumn, EditableTaskField, TaskTemplateOption } from "@/features/weekly-report/task-editing"
import type { HumanResourcesTaskAttachment } from "../types"
import { formatDateTime } from "@/utils/date"
import TemplateTaskCell from "@/features/weekly-report/components/TemplateTaskCell.vue"
import TaskInlineField from "@/features/weekly-report/components/TaskInlineField.vue"
import TaskEvidenceDialog from "@/features/weekly-report/components/TaskEvidenceDialog.vue"
import ModuleCell from "./ModuleCell.vue"
import TaskTextFieldDialog from "./TaskTextFieldDialog.vue"
const props = defineProps<{ entries: { task: T; index: number }[]; fields: EditableTaskField[]; users: DirectoryUserOption[]; offset: number; totalTasks?: number; templates: readonly TaskTemplateOption[] }>()
const resizeKey = useTaskTableResizeKey("weekly", () => "human_resources_v1")
const emit = defineEmits<{ addBlank: []; patch: [key: string, value: Partial<EditableTask>]; insert: [index: number, shared?: "dimension" | "task_name" | "work_content"]; remove: [index: number] }>()
const textFields: EditableTaskColumn[] = ["task_name", "work_content", "output_description", "progress_text", "delay_reason", "document_links"]
const editing = ref<{ key: string; field: EditableTaskColumn; value: string } | null>(null)
const evidence = ref<{ key: string; links: string; attachments: HumanResourcesTaskAttachment[] } | null>(null)
const editingTitle = computed(() => editing.value?.field === "dimension" ? "模块" : editing.value?.field === "task_name" ? "工作事项" : props.fields.find(field => field.code === editing.value?.field)?.label || "内容")
const templateField = computed(() => {
  const field = editing.value?.field
  return field === "dimension" || field === "task_name" || field === "work_content" ? field : undefined
})
function editText(task: EditableTask, field: EditableTaskColumn) {
  if (field === "document_links") { editEvidence(task); return }
  editing.value = { key: task.client_key, field, value: String(task[field] || "") }
}
function editEvidence(task: EditableTask) {
  evidence.value = { key: task.client_key, links: task.document_links, attachments: task.attachments.map(item => ({ ...item })) }
}
function saveEvidence(links: string, attachments: HumanResourcesTaskAttachment[]) {
  if (!evidence.value) return
  emit("patch", evidence.value.key, { document_links: links, attachments })
  evidence.value = null
}
function saveText(value: string, index?: number) {
  if (!editing.value) return
  const patch: Partial<EditableTask> = { [editing.value.field]: value }
  const template = index === undefined ? undefined : props.templates[index]
  const task = props.entries.find(entry => entry.task.client_key === editing.value?.key)?.task
  if (template && task) {
    if (editing.value.field === "dimension" || !task.dimension?.trim()) Object.assign(patch, {
      dimension: template.dimension || "", dimension_source: "template", dimension_template: template.dimension || "", dimension_values: [],
    })
    if (editing.value.field === "task_name" || !task.task_name.trim()) Object.assign(patch, {
      task_name: template.task, task_source: "template", task_template: template.task, task_values: Array((template.task.match(/[?？]/g) || []).length).fill(""),
    })
    if (editing.value.field !== "work_content" && !task.work_content) patch.work_content = template.work
  }
  emit("patch", editing.value.key, patch); editing.value = null
}
function key(task: EditableTask, field: "dimension" | "task_name" | "work_content") {
  const module = task.dimension_text_id || task.dimension_group_key || task.client_key
  const taskKey = `${module}:${task.task_text_id || task.task_group_key || task.client_key}`
  return field === "dimension" ? module : field === "task_name" ? taskKey : `${taskKey}:${task.work_content_text_id || task.work_content_group_key || task.client_key}`
}
function spanRows(index: number, field: "dimension" | "task_name" | "work_content") {
  const group = key(props.entries[index]!.task, field)
  if (index && key(props.entries[index - 1]!.task, field) === group) return 0
  let count = 1
  while (index + count < props.entries.length && key(props.entries[index + count]!.task, field) === group) count++
  return count
}
</script>
<template>
  <div class="editable-table-wrap"><table v-row-backgrounds v-resizable-columns="resizeKey" class="editable-task-table delivery-mode">
    <thead><tr><th class="serial-col" data-column-key="serial">序号</th><th data-column-key="dimension" class="customer-col">模块</th><th class="task-col" data-column-key="task_name">工作事项</th><th :data-column-key="field.code" v-for="field in fields" :key="field.code" class="value-col" :class="{ 'multiline-col': textFields.includes(field.code) }">{{ field.label }}</th><th class="date-col" data-column-key="updated_at">更新时间</th><th class="actions-col" data-column-key="actions">操作</th></tr></thead>
    <tbody><tr v-for="(entry, index) in entries" :key="entry.task.client_key" :class="{ 'blank-row': !entry.task.task_name }">
      <td class="serial-col">{{ offset + index + 1 }}</td>
      <td v-if="spanRows(index, 'dimension')" :rowspan="spanRows(index, 'dimension')" class="customer-col shared-cell"><ModuleCell v-if="entry.task.dimension_source === 'template'" :task="entry.task" @patch="emit('patch', entry.task.client_key, $event)" /><button v-else class="text-cell user-content" type="button" @click="editText(entry.task, 'dimension')">{{ entry.task.dimension || '点击填写模块' }}</button><button data-task-tip="新增工作任务" aria-label="新增工作任务" class="cell-insert" type="button" @click="emit('insert', entry.index, 'dimension')"><Plus :size="16" /></button></td>
      <td v-if="spanRows(index, 'task_name')" :rowspan="spanRows(index, 'task_name')" class="task-col shared-cell"><TemplateTaskCell v-if="entry.task.task_source === 'template'" label="工作事项" :task="entry.task" @patch="emit('patch', entry.task.client_key, $event)" /><button v-else class="text-cell user-content" type="button" @click="editText(entry.task, 'task_name')">{{ entry.task.task_name || '点击填写工作事项' }}</button><button data-task-tip="新增工作内容" aria-label="新增工作内容" class="cell-insert" type="button" @click="emit('insert', entry.index, 'task_name')"><Plus :size="16" /></button></td>
      <template v-for="field in fields" :key="field.code"><td v-if="field.code !== 'work_content' || spanRows(index, 'work_content')" :rowspan="field.code === 'work_content' ? spanRows(index, 'work_content') : 1" class="value-col" :class="{ 'multiline-col': textFields.includes(field.code), 'shared-cell': field.code === 'work_content' }">
        <button v-if="textFields.includes(field.code)" class="text-cell user-content" type="button" @click="editText(entry.task, field.code)">{{ entry.task[field.code] || `点击填写${field.label}` }}</button>
        <TaskInlineField v-else :task="entry.task" :field="field.code" :label="field.label" :users="users" @patch="emit('patch', entry.task.client_key, $event)" />
        <button data-task-tip="新增输出成果" aria-label="新增输出成果" v-if="field.code === 'work_content'" class="cell-insert" type="button" @click="emit('insert', entry.index, 'work_content')"><Plus :size="16" /></button>
      </td></template>
      <td class="date-col">{{ formatDateTime(entry.task.updated_at) }}</td><td class="actions-col"><div class="row-actions"><button class="link-button danger" type="button" @click="emit('remove', entry.index)">删除</button><button data-task-tip="新增自定义任务" aria-label="新增自定义任务" class="insert-button" type="button" @click="emit('insert', entry.index)"><Plus :size="17" /></button></div></td>
    </tr><tr v-if="!entries.length"><td :colspan="fields.length + 5" class="empty"><div class="empty-task-content"><p>{{ totalTasks ? '当前筛选条件下暂无任务' : '暂无工作任务' }}</p><button v-if="!totalTasks" class="empty-task-button" type="button" @click="emit('addBlank')"><Plus :size="18" />新增自定义任务</button></div></td></tr></tbody>
  </table></div>
  <TaskTextFieldDialog :open="Boolean(editing)" :title="editingTitle" :value="editing?.value || ''" :template-field="templateField" :templates="templates" :max-length="editing?.field === 'dimension' ? 255 : undefined" @close="editing = null" @save="saveText" />
  <TaskEvidenceDialog :open="Boolean(evidence)" :links="evidence?.links || ''" :attachments="evidence?.attachments || []" @close="evidence = null" @save="saveEvidence" />
</template>
<style scoped src="./EditableTaskTable.css"></style>
