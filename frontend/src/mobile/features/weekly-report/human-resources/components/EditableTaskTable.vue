<script setup lang="ts" generic="T extends EditableTask">
import TaskHierarchy from "@/mobile/components/data-display/TaskHierarchy.vue"
import { computed, ref } from "vue"
import { Plus } from "lucide-vue-next"
import type { DirectoryUserOption } from "@/mobile/features/directory/types"
import type { EditableTask, EditableTaskColumn, EditableTaskField, TaskTemplateOption } from "@/mobile/features/weekly-report/task-editing"
import type { HumanResourcesTaskAttachment } from "../types"
import { formatDateTime } from "@/utils/date"
import TemplateTaskCell from "@/mobile/features/weekly-report/components/TemplateTaskCell.vue"
import TaskInlineField from "@/mobile/features/weekly-report/components/TaskInlineField.vue"
import TaskEvidenceDialog from "@/mobile/features/weekly-report/components/TaskEvidenceDialog.vue"
import ModuleCell from "./ModuleCell.vue"
import TaskTextFieldDialog from "./TaskTextFieldDialog.vue"
const props = defineProps<{ allTasks?: T[]
  entries: { task: T; index: number }[]; fields: EditableTaskField[]; users: DirectoryUserOption[]; offset: number; totalTasks?: number; templates: readonly TaskTemplateOption[] }>()
const emit = defineEmits<{ addBlank: []; patch: [key: string, value: Partial<EditableTask>]; insert: [index: number, shared?: "dimension" | "task_name" | "work_content"]; removeMany: [keys: string[]]; remove: [index: number] }>()
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
</script>
<template>
  <div class="editable-table-wrap"><div class="mobile-task-cards">
    
    <TaskHierarchy deletable :all-rows="allTasks?.map((task, index) => ({task, index}))" @remove="items => emit('removeMany', items.map(item => item.task.client_key))" :rows="entries" :row-key="row => row.task.client_key" :task-key="row => `${row.task.dimension_text_id || row.task.dimension_group_key || ''}:${row.task.task_text_id || row.task.task_group_key || row.task.client_key}`" :content-key="row => row.task.work_content_text_id || row.task.work_content_group_key || row.task.client_key" :title="row => row.task.task_name">
 <template #task="{row:entry,index}">
      
      <div data-card-field data-label="模块"  class="customer-col shared-cell"><ModuleCell v-if="entry.task.dimension_source === 'template'" :task="entry.task" @patch="emit('patch', entry.task.client_key, $event)" /><button v-else class="text-cell user-content" type="button" @click="editText(entry.task, 'dimension')">{{ entry.task.dimension || '点击填写模块' }}</button><button data-task-tip="新增工作任务" aria-label="新增工作任务" class="cell-insert" type="button" @click="emit('insert', entry.index, 'dimension')"><Plus :size="16" /><span>新增工作任务</span></button></div>
      <div data-card-field data-label="工作事项"  class="task-col shared-cell"><TemplateTaskCell v-if="entry.task.task_source === 'template'" label="工作事项" :task="entry.task" @patch="emit('patch', entry.task.client_key, $event)" /><button v-else class="text-cell user-content" type="button" @click="editText(entry.task, 'task_name')">{{ entry.task.task_name || '点击填写工作事项' }}</button><button data-task-tip="新增工作内容" aria-label="新增工作内容" class="cell-insert" type="button" @click="emit('insert', entry.index, 'task_name')"><Plus :size="16" /><span>新增工作内容</span></button></div>
      </template>
 <template #content="{row:entry,index}"><template v-for="field in fields.filter(item => item.code === 'work_content')" :key="field.code"><div data-card-field :data-label="field.label"  class="value-col" :class="{ 'multiline-col': textFields.includes(field.code), 'shared-cell': field.code === 'work_content' }">
        <button v-if="textFields.includes(field.code)" class="text-cell user-content" type="button" @click="editText(entry.task, field.code)">{{ entry.task[field.code] || `点击填写${field.label}` }}</button>
        <TaskInlineField v-else :task="entry.task" :field="field.code" :label="field.label" :users="users" @patch="emit('patch', entry.task.client_key, $event)" />
        <button v-if="field.code === 'document_links'" type="button" class="link-button attachment-button" @click="editEvidence(entry.task)">{{ entry.task.attachments.length ? `${entry.task.attachments.length} 个附件` : '管理附件' }}</button>
        <button data-task-tip="新增输出成果" aria-label="新增输出成果" v-if="field.code === 'work_content'" class="cell-insert" type="button" @click="emit('insert', entry.index, 'work_content')"><Plus :size="16" /><span>新增工作成果与进度</span></button>
      </div></template>
      </template>
 <template #row="{row:entry,index}"><template v-for="field in fields.filter(item => item.code !== 'work_content')" :key="field.code"><div data-card-field :data-label="field.label"  class="value-col" :class="{ 'multiline-col': textFields.includes(field.code), 'shared-cell': field.code === 'work_content' }">
        <button v-if="textFields.includes(field.code)" class="text-cell user-content" type="button" @click="editText(entry.task, field.code)">{{ entry.task[field.code] || `点击填写${field.label}` }}</button>
        <TaskInlineField v-else :task="entry.task" :field="field.code" :label="field.label" :users="users" @patch="emit('patch', entry.task.client_key, $event)" />
        <button v-if="field.code === 'document_links'" type="button" class="link-button attachment-button" @click="editEvidence(entry.task)">{{ entry.task.attachments.length ? `${entry.task.attachments.length} 个附件` : '管理附件' }}</button>
        <button data-task-tip="新增输出成果" aria-label="新增输出成果" v-if="field.code === 'work_content'" class="cell-insert" type="button" @click="emit('insert', entry.index, 'work_content')"><Plus :size="16" /><span>新增工作成果与进度</span></button>
      </div></template>
      <div data-card-field data-label="更新时间" class="date-col">{{ formatDateTime(entry.task.updated_at) }}</div><div data-card-field data-label="" class="actions-col"><div class="row-actions"></div></div>
    </template>
</TaskHierarchy><p v-if="!entries.length && totalTasks" class="filtered-empty">当前筛选条件下暂无任务</p>
  </div></div>
  <TaskTextFieldDialog :open="Boolean(editing)" :title="editingTitle" :value="editing?.value || ''" :template-field="templateField" :templates="templates" :max-length="editing?.field === 'dimension' ? 255 : undefined" @close="editing = null" @save="saveText" />
  <TaskEvidenceDialog :open="Boolean(evidence)" :links="evidence?.links || ''" :attachments="evidence?.attachments || []" @close="evidence = null" @save="saveEvidence" />
</template>
<style scoped src="./EditableTaskTable.css"></style>

<style scoped src="@/mobile/components/data-display/TaskCards.css"></style>



