<script setup lang="ts" generic="T extends EditableTask">
import { vResizableColumns } from "@/shared/table/resizable-columns"
import { useTaskTableResizeKey } from "@/features/weekly-report/useTaskTableResizeKey"
import { computed, ref } from "vue"
import { Plus } from "lucide-vue-next"
import type { DirectoryUserOption } from "@/features/directory/types"
import type { EditableTask, EditableTaskColumn, EditableTaskField, TaskTemplateOption } from "@/features/weekly-report/task-editing"
import { formatDateTime } from "@/utils/date"
import TemplateCustomerCell from "./TemplateCustomerCell.vue"
import TemplateDimensionCell from "./TemplateDimensionCell.vue"
import TemplateTaskCell from "./TemplateTaskCell.vue"
import TaskInlineField from "./TaskInlineField.vue"
import TaskTextFieldDialog from "@/features/weekly-report/components/TaskTextFieldDialog.vue"
import TaskEvidenceDialog from "./TaskEvidenceDialog.vue"
import type { TaskAttachment } from "@/features/weekly-report/task-draft"

const props = withDefaults(defineProps<{
  entries: { task: T; index: number }[]
  fields: EditableTaskField[]
  users: DirectoryUserOption[]
  offset: number
  templateCode?: string
  totalTasks?: number
  deliveryMode?: boolean
  recruitmentMode?: boolean
  salesMode?: boolean
  scopeLabel?: string
  scopeField?: "customer_name" | "dimension"
  templates?: readonly TaskTemplateOption[]
}>(), { scopeField: "customer_name", templates: () => [] })
const resizeKey = useTaskTableResizeKey("weekly", () => props.templateCode)
const emit = defineEmits<{
  addBlank: []
  patch: [key: string, value: Partial<EditableTask>]
  insert: [index: number, shared?: "customer_name" | "dimension" | "task_name" | "work_content"]
  edit: [index: number]
  remove: [index: number]
  view: [task: T]
}>()
const displayScopeLabel = computed(() => props.scopeLabel || (props.scopeField === "dimension" ? "维度" : "客户"))
const textFields: EditableTaskColumn[] = ["task_name", "work_content", "output_description", "progress_text", "delay_reason", "document_links"]
const editing = ref<{ key: string; field: EditableTaskColumn; value: string } | null>(null)
const evidence = ref<{ key: string; links: string; attachments: TaskAttachment[] } | null>(null)
const editingTitle = computed(() => editing.value ? (editing.value.field === "customer_name" ? displayScopeLabel.value : editing.value.field === "dimension" ? "维度" : editing.value.field === "task_name" ? "工作任务" : props.fields.find(field => field.code === editing.value?.field)?.label || "内容") : "")
const templateField = computed(() => {
  const field = editing.value?.field
  return field === "customer_name" || field === "dimension" || field === "task_name" || field === "work_content" ? field : undefined
})
function editText(task: EditableTask, field: EditableTaskColumn) {
  if (field === "document_links") { editEvidence(task); return }
  editing.value = { key: task.client_key, field, value: String(task[field] || "") }
}
function editEvidence(task: EditableTask) {
  evidence.value = { key: task.client_key, links: task.document_links, attachments: task.attachments.map(item => ({ ...item })) }
}
function saveEvidence(links: string, attachments: TaskAttachment[]) {
  if (!evidence.value) return
  emit("patch", evidence.value.key, { document_links: links, attachments })
  evidence.value = null
}
function saveText(value: string, templateIndex?: number) {
  if (!editing.value) return
  const patch: Partial<EditableTask> = { [editing.value.field]: value }
  const template = templateIndex === undefined ? undefined : props.templates[templateIndex]
  const task = props.entries.find(entry => entry.task.client_key === editing.value?.key)?.task
  if (template && task && templateField.value) {
    if ((props.deliveryMode || props.recruitmentMode || props.salesMode) && (editing.value.field === "task_name" || !task.task_name.trim())) {
      Object.assign(patch, { task_source: "template", task_template: template.task, task_values: Array(template.task.split(/[?？]/).length - 1).fill("") })
    }
    if (props.salesMode && (editing.value.field === "customer_name" || !task.customer_name?.trim())) {
      Object.assign(patch, { customer_name: template.customer || "", customer_source: "template", customer_template: template.customer || "", customer_values: Array((template.customer || "").split(/[?？]/).length - 1).fill("") })
    }
    if (props.recruitmentMode && (editing.value.field === "dimension" || !task.dimension?.trim())) {
      Object.assign(patch, { dimension: template.dimension || "", dimension_source: "template", dimension_template: template.dimension || "", dimension_values: Array((template.dimension || "").split(/[?？]/).length - 1).fill("") })
    } else if (props.scopeField === "dimension" && editing.value.field !== "dimension" && !task.dimension?.trim()) patch.dimension = template.dimension || ""
    for (const [field, content] of [["task_name", template.task], ["work_content", template.work]] as const) {
      if (field !== editing.value.field && !task[field].trim()) patch[field] = content
    }
  }
  emit("patch", editing.value.key, patch)
  editing.value = null
}
function group(index: number, field: "customer_name" | "dimension" | "task_name" | "work_content") {
  const task = props.entries[index]?.task
  if (!task) return ""
  const dimensionKey = props.salesMode ? `${task.customer_text_id || task.customer_group_key || task.client_key}:` : props.recruitmentMode ? `${task.dimension_text_id || task.dimension_group_key || task.client_key}:` : ""
  if (field === "dimension" || field === "customer_name") return dimensionKey
  const taskKey = dimensionKey + (task.task_text_id || task.task_group_key || task.client_key)
  return field === "task_name" ? taskKey : `${taskKey}:${task.work_content_text_id || task.work_content_group_key || task.client_key}`
}
function spanRows(index: number, field: "customer_name" | "dimension" | "task_name" | "work_content") {
  if (!props.deliveryMode && !props.recruitmentMode && !props.salesMode) return 1
  const key = group(index, field)
  if (index > 0 && group(index - 1, field) === key) return 0
  let count = 1
  while (index + count < props.entries.length && group(index + count, field) === key) count++
  return count
}
</script>
<template>
  <div class="editable-table-wrap">
    <table v-row-backgrounds v-resizable-columns="resizeKey" class="editable-task-table" :class="{ 'delivery-mode': deliveryMode || recruitmentMode || salesMode }">
      <thead><tr><th class="serial-col" data-column-key="serial">序号</th><th :data-column-key="scopeField" v-if="!deliveryMode" class="customer-col">{{ displayScopeLabel }}</th><th class="task-col" data-column-key="task_name">工作任务</th><th :data-column-key="field.code" v-for="field in fields" :key="field.code" class="value-col" :class="{ 'multiline-col': textFields.includes(field.code) }">{{ field.label }}</th><th class="date-col" data-column-key="updated_at">更新时间</th><th class="actions-col" data-column-key="actions">操作</th></tr></thead>
      <tbody>
        <tr v-for="(entry, index) in entries" :key="entry.task.client_key" :class="{ 'blank-row': !entry.task.task_name }">
          <td class="serial-col">{{ offset + index + 1 }}</td>
          <td v-if="!deliveryMode && (!(recruitmentMode || salesMode) || spanRows(index, salesMode ? 'customer_name' : 'dimension'))" class="customer-col" :class="{ 'shared-cell': recruitmentMode || salesMode }" :rowspan="recruitmentMode || salesMode ? spanRows(index, salesMode ? 'customer_name' : 'dimension') : 1"><TemplateCustomerCell v-if="salesMode && entry.task.customer_source === 'template'" :task="entry.task" :label="displayScopeLabel" @patch="emit('patch', entry.task.client_key, $event)" /><button v-else-if="salesMode" class="text-cell user-content" type="button" :aria-label="`编辑第 ${offset + index + 1} 行${displayScopeLabel}`" @click="editText(entry.task, 'customer_name')">{{ entry.task.customer_name || `点击填写${displayScopeLabel}` }}</button><TemplateDimensionCell v-else-if="recruitmentMode && entry.task.dimension_source === 'template'" :task="entry.task" @patch="emit('patch', entry.task.client_key, $event)" /><button v-else-if="scopeField === 'dimension'" class="text-cell user-content" type="button" :aria-label="`编辑第 ${offset + index + 1} 行维度`" @click="editText(entry.task, 'dimension')">{{ entry.task.dimension || '点击填写维度' }}</button><TaskInlineField v-else :task="entry.task" field="customer_name" label="客户" :users="users" @patch="emit('patch', entry.task.client_key, $event)" /><button data-task-tip="新增工作任务" aria-label="新增工作任务" v-if="recruitmentMode || salesMode" class="cell-insert" type="button" @click.stop="emit('insert', entry.index, salesMode ? 'customer_name' : 'dimension')"><Plus :size="16" /></button></td>
          <td v-if="spanRows(index, 'task_name')" class="task-col" :class="{ 'shared-cell': deliveryMode || recruitmentMode || salesMode }" :rowspan="spanRows(index, 'task_name')">
            <TemplateTaskCell v-if="(deliveryMode || recruitmentMode || salesMode) && entry.task.task_source === 'template'" :task="entry.task" @patch="emit('patch', entry.task.client_key, $event)" />
            <button v-else class="text-cell user-content" type="button" :aria-label="`编辑第 ${offset + index + 1} 行工作任务`" @click="editText(entry.task, 'task_name')">{{ entry.task.task_name || '点击填写工作任务' }}</button>
            <button data-task-tip="新增工作内容" aria-label="新增工作内容" v-if="deliveryMode || recruitmentMode || salesMode" class="cell-insert" type="button" @click.stop="emit('insert', entry.index, 'task_name')"><Plus :size="16" /></button>
          </td>
          <template v-for="field in fields" :key="field.code"><td v-if="field.code !== 'work_content' || spanRows(index, 'work_content')" :rowspan="field.code === 'work_content' ? spanRows(index, 'work_content') : 1" class="value-col" :class="{ 'multiline-col': textFields.includes(field.code), 'shared-cell': (deliveryMode || recruitmentMode || salesMode) && field.code === 'work_content' }">
            <button v-if="textFields.includes(field.code)" class="text-cell user-content" type="button" :aria-label="`编辑第 ${offset + index + 1} 行${field.label}`" @click="editText(entry.task, field.code)">{{ entry.task[field.code] || `点击填写${field.label}` }}</button>
            <TaskInlineField v-else :task="entry.task" :field="field.code" :label="field.label" :users="users" @patch="emit('patch', entry.task.client_key, $event)" />
            <button v-if="field.code === 'document_links'" type="button" class="link-button attachment-button" @click="editEvidence(entry.task)">{{ entry.task.attachments.length ? `${entry.task.attachments.length} 个附件` : '管理附件' }}</button>
            <button data-task-tip="新增输出成果" aria-label="新增输出成果" v-if="(deliveryMode || recruitmentMode || salesMode) && field.code === 'work_content'" class="cell-insert" type="button" @click.stop="emit('insert', entry.index, 'work_content')"><Plus :size="16" /></button>
          </td></template>
          <td class="date-col">{{ formatDateTime(entry.task.updated_at) }}</td>
          <td class="actions-col"><div class="row-actions"><button v-if="!deliveryMode && !recruitmentMode && !salesMode" type="button" class="link-button" @click="emit('view', entry.task)">查看</button><button v-if="!deliveryMode && !recruitmentMode && !salesMode" type="button" class="link-button" @click="emit('edit', entry.index)">编辑</button><button type="button" class="link-button danger" @click="emit('remove', entry.index)">删除</button><button data-task-tip="新增自定义任务" aria-label="新增自定义任务" type="button" class="insert-button" @click="emit('insert', entry.index)"><Plus :size="17" aria-hidden="true" /></button></div></td>
        </tr>
        <tr v-if="!entries.length"><td :colspan="fields.length + (deliveryMode ? 4 : 5)" class="empty"><div class="empty-task-content">
          <p>{{ totalTasks ? '当前筛选条件下暂无任务' : '暂无工作任务' }}</p>
          <div v-if="!totalTasks" class="empty-task-actions">
            <button class="empty-task-button" type="button" @click="emit('addBlank')"><Plus :size="18" aria-hidden="true" />新增自定义任务</button>
          </div>
        </div></td></tr>
      </tbody>
    </table>
  </div>
  <TaskTextFieldDialog :open="Boolean(editing)" :title="editingTitle" :value="editing?.value || ''" :template-field="templateField" :templates="templates" :customer-label="displayScopeLabel" :max-length="editing?.field === 'dimension' ? 64 : undefined" @close="editing = null" @save="saveText" />
  <TaskEvidenceDialog :open="Boolean(evidence)" :links="evidence?.links || ''" :attachments="evidence?.attachments || []" @close="evidence = null" @save="saveEvidence" />
</template>
<style scoped src="./EditableTaskTable.css"></style>
