<script setup lang="ts">
import { vRowBackgrounds } from "@/shared/table/row-backgrounds"
import CustomerTabsHeader from "@/features/submissions/components/CustomerTabsHeader.vue"
import { vResizableColumns } from "@/shared/table/resizable-columns"
import { useTaskTableResizeKey } from "@/features/weekly-report/useTaskTableResizeKey"
import FullscreenPanel from "@/components/layout/FullscreenPanel.vue"
import MonthlyPlanTaskCells from "@/features/monthly-plan/components/MonthlyPlanTaskCells.vue"
import MonthlyPlanFieldDialog from "@/features/monthly-plan/components/MonthlyPlanFieldDialog.vue"
import { useMonthlyTaskFields } from "@/features/monthly-plan/useMonthlyTaskFields"
import { formatDateTime } from "@/utils/date"
import { computed, ref, watch } from "vue"
import { Plus } from "lucide-vue-next"
import ExamplePreviewButton from "@/components/feedback/ExamplePreviewButton.vue"
import PaginationBar from "@/components/navigation/PaginationBar.vue"
import { createId } from "@/utils/id"
import { expandMonthlyTasks, insertMonthlyChild, monthlyRowSpan, patchMonthlyTasks, type MonthlyGroupLevel } from "@/features/monthly-plan/task-groups"
import type { MonthlyPlanTask } from "@/features/weekly-report/monthly-plan/types"
import { previewTaskTemplate } from "@/features/weekly-report/task-texts"
import TemplateTaskCell from "@/features/weekly-report/components/TemplateTaskCell.vue"
import { humanResourcesMonthlyTaskTemplates } from "../task-templates"
import { humanResourcesMonthlyTaskSampleFields } from "../samples"
import TaskQuickFillDialog from "./TaskQuickFillDialog.vue"
import TaskTextFieldDialog from "./TaskTextFieldDialog.vue"
import { updateMonthlyTaskProgress } from "@/features/monthly-plan/api"
import { getErrorMessage } from "@/shared/api/errors"
const props = defineProps<{ tasks: MonthlyPlanTask[]; monthKey: string; templateCode?: string; readonly?: boolean; progressEditable?: boolean; disabled?: boolean; isLoading?: boolean; errorMessage?: string }>()
const resizeKey = useTaskTableResizeKey("monthly", () => "human_resources_v1")
const emit = defineEmits<{ "update:tasks": [tasks: MonthlyPlanTask[]]; retry: [] }>()
const { users, columnsOpen, selected, availableFields, selectedFields, fieldError, reloadFields } = useMonthlyTaskFields(() => props.templateCode || "human_resources_v1")
const rows = computed(() => expandMonthlyTasks(props.tasks))
const progressBusy = ref(false)
const progressError = ref("")
const progressSaved = ref(false)
const unavailable = computed(() => props.disabled || props.isLoading || Boolean(props.errorMessage) || progressBusy.value)
const blocked = computed(() => props.readonly || unavailable.value)
const liveProgressFields = new Set(["progress_text", "progress_percent", "quality_percent", "completion_rate", "delay_reason", "on_time_status", "actual_completion_date", "owner_id", "owner_name", "collaborator_names", "document_links"])
async function saveLiveProgress(id: string, fields: Partial<MonthlyPlanTask>) {
  const current = props.tasks.find(task => task.id === id)
  if (!current || !/^\d+$/.test(id) || Object.keys(fields).some(field => !liveProgressFields.has(field))) return
  progressBusy.value = true; progressError.value = ""; progressSaved.value = false
  try {
    const result = await updateMonthlyTaskProgress(id, { ...fields, revision: current.progress_revision || 0 })
    const updated = { ...current, ...result.values, progress_revision: result.revision, progress_updated_at: result.updated_at || null, progress_updated_by: result.updated_by || null, progress_updated_by_name: result.updated_by_name || "" }
    emit("update:tasks", props.tasks.map(task => task.id === id ? updated : task)); progressSaved.value = true
  } catch (cause) { progressError.value = getErrorMessage(cause) }
  finally { progressBusy.value = false }
}
const page = ref(1), pageSize = 10
const totalPages = computed(() => Math.max(1, Math.ceil(rows.value.length / pageSize)))
const entries = computed(() => rows.value.slice((page.value - 1) * pageSize, page.value * pageSize))
watch(totalPages, value => { page.value = Math.min(page.value, value) })
watch([rows, blocked], ([tasks, stop]) => { if (!stop && tasks.some((task, index) => task !== props.tasks[index])) emit("update:tasks", tasks) }, { immediate: true })
const quickFillOpen = ref(false)
const editing = ref<{ task: MonthlyPlanTask; field: "scope_name" | "work_task" | "work_content" } | null>(null)
const title = computed(() => editing.value?.field === "scope_name" ? "模块" : editing.value?.field === "work_content" ? "工作内容" : "工作事项")
function patch(id: string, fields: Partial<MonthlyPlanTask>) {
  if (unavailable.value || (props.readonly && !props.progressEditable)) return
  const current = rows.value.find(task => task.id === id)
  if (current && ("progress_percent" in fields || "quality_percent" in fields)) fields.completion_rate = Math.round((Number(fields.progress_percent ?? current.progress_percent ?? 0) + Number(fields.quality_percent ?? current.quality_percent ?? 0)) / 2)
  if (props.readonly) { void saveLiveProgress(id, fields); return }
  emit("update:tasks", patchMonthlyTasks(rows.value, id, fields))
}
function insert(id: string, level?: MonthlyGroupLevel) {
  if (blocked.value) return
  if (level) emit("update:tasks", insertMonthlyChild(rows.value, id, level))
  else {
    const tasks = [...rows.value], index = tasks.findIndex(task => task.id === id)
    tasks.splice(index + 1, 0, { id: `draft-${createId()}`, scope_name: "", work_task: "", work_content: "", task_source: "custom" })
    emit("update:tasks", tasks)
  }
}
function add(_: string, indexes: number[]) {
  if (blocked.value) return
  const modules = new Map<string, string>()
  const tasks = indexes.flatMap(index => {
    const template = humanResourcesMonthlyTaskTemplates[index]!, scope = modules.get(template.dimension) || createId()
    modules.set(template.dimension, scope)
    return expandMonthlyTasks([{ id: `draft-${createId()}`, scope_name: template.dimension, scope_group_key: scope,
      work_task: template.task, work_content: template.work, task_source: "template", task_template: template.task,
      task_values: Array((template.task.match(/[?？]/g) || []).length).fill(""), dimension_source: "template",
      dimension_template: template.dimension, dimension_values: Array((template.dimension.match(/[?？]/g) || []).length).fill(""),
    }])
  })
  emit("update:tasks", [...rows.value, ...tasks]); quickFillOpen.value = false
}
function saveText(value: string, index?: number) {
  const edit = editing.value
  if (!edit) return
  const template = index === undefined ? undefined : humanResourcesMonthlyTaskTemplates[index]
  const fields: Partial<MonthlyPlanTask> = { [edit.field]: value }
  if (template) {
    if (edit.field === "scope_name" || !edit.task.scope_name) Object.assign(fields, { scope_name: template.dimension, dimension_source: "template", dimension_template: template.dimension, dimension_values: [] })
    if (edit.field === "work_task" || !edit.task.work_task) Object.assign(fields, { work_task: template.task, task_source: "template", task_template: template.task, task_values: [] })
    if (edit.field !== "work_content" && !edit.task.work_content) fields.work_content = template.work
  } else if (edit.field === "work_task") Object.assign(fields, { task_source: "custom", task_template: "", task_values: [] })
  patch(edit.task.id, fields); editing.value = null
}
</script>
<template>
  <FullscreenPanel title="月度计划" class="dashboard-card monthly-task-panel">
    <template #tabs><CustomerTabsHeader /></template>
    <template #actions>
      <span v-if="readonly && progressEditable" class="live-progress-hint">右侧为实时进度，保存后无需重新审批</span>
      <button class="ghost-button" type="button" @click="columnsOpen = true">选择展示字段</button>
      <template v-if="!readonly">
        <ExamplePreviewButton content="" :fields="humanResourcesMonthlyTaskSampleFields" panel-title="人资月度计划填写样例" />
        <button class="primary-button" type="button" :disabled="blocked" @click="quickFillOpen = true">新增计划</button>
      </template>
    </template>
    <div v-if="isLoading" class="monthly-task-empty">正在加载月度计划…</div>
    <div v-else-if="errorMessage" class="monthly-task-empty"><p>{{ errorMessage }}</p><button class="ghost-button" type="button" @click="emit('retry')">重试</button></div>
    <template v-else><p v-if="progressBusy" class="live-progress-message" aria-live="polite">正在保存实时进度…</p><p v-else-if="progressError" class="live-progress-message error" role="alert">{{ progressError }}</p><p v-else-if="progressSaved" class="live-progress-message success" aria-live="polite">实时进度已保存，计划基线和审批状态未改变。</p><p v-if="fieldError" role="alert">{{ fieldError }} <button class="ghost-button" type="button" @click="reloadFields">重试</button></p><div class="monthly-task-table-wrap"><table v-row-backgrounds v-resizable-columns="resizeKey" class="monthly-task-table delivery-table" :style="{ minWidth: `${800 + selectedFields.length * 210}px` }"><thead><tr><th class="serial" data-column-key="serial">序号</th><th data-column-key="scope_name" class="customer">模块</th><th data-column-key="task_name">工作事项</th><th :data-column-key="field.code" v-for="field in selectedFields" :key="field.code">{{ field.label }}</th><th data-column-key="updated_at">更新时间</th><th v-if="!readonly" class="actions" data-column-key="actions">操作</th></tr></thead><tbody>
      <tr v-for="(task, index) in entries" :key="task.id"><td class="serial">{{ (page - 1) * pageSize + index + 1 }}</td>
        <td v-if="monthlyRowSpan(entries, index, 'scope')" :rowspan="monthlyRowSpan(entries, index, 'scope')" class="shared-monthly-cell"><span v-if="blocked" class="monthly-task-plain user-content">{{ task.scope_name || '—' }}</span><TemplateTaskCell v-else-if="task.dimension_source === 'template'" label="模块" :task="{ task_name: task.scope_name || '', task_template: task.dimension_template, task_values: task.dimension_values }" @patch="patch(task.id, { scope_name: $event.task_name, dimension_values: $event.task_values })" /><button v-else class="monthly-task-text-cell user-content" type="button" @click="editing = { task, field: 'scope_name' }">{{ task.scope_name || '点击填写模块' }}</button><button data-task-tip="新增工作任务" aria-label="新增工作任务" v-if="!blocked" class="cell-insert" type="button" @click="insert(task.id, 'scope')"><Plus :size="16" /></button></td>
        <td v-if="monthlyRowSpan(entries, index, 'task')" :rowspan="monthlyRowSpan(entries, index, 'task')" class="shared-monthly-cell"><span v-if="blocked" class="monthly-task-plain user-content">{{ task.task_source === 'template' ? previewTaskTemplate(task.task_template || '', task.task_values || []) : task.work_task || '—' }}</span><TemplateTaskCell v-else-if="task.task_source === 'template'" label="工作事项" :task="{ task_name: task.work_task, task_template: task.task_template, task_values: task.task_values }" @patch="patch(task.id, { work_task: $event.task_name, task_values: $event.task_values })" /><button v-else class="monthly-task-text-cell user-content" type="button" @click="editing = { task, field: 'work_task' }">{{ task.work_task || '点击填写工作事项' }}</button><button data-task-tip="新增工作内容" aria-label="新增工作内容" v-if="!blocked" class="cell-insert" type="button" @click="insert(task.id, 'task')"><Plus :size="16" /></button></td>
        <MonthlyPlanTaskCells :task="task" :fields="selectedFields" :users="users" :readonly="blocked" :progress-editable="Boolean(progressEditable) && !unavailable" :content-span="monthlyRowSpan(entries, index, 'content')" @patch="patch(task.id, $event)" @insert-content="insert(task.id, 'content')" />
        <td>{{ formatDateTime(task.progress_updated_at || task.updated_at) }}</td>
        <td v-if="!readonly" class="actions"><button class="link-button danger" type="button" :disabled="blocked" @click="emit('update:tasks', rows.filter(row => row.id !== task.id))">删除</button><button data-task-tip="新增自定义计划" aria-label="新增自定义计划" class="link-button insert-button" type="button" :disabled="blocked" @click="insert(task.id)"><Plus :size="18" /></button></td>
      </tr><tr v-if="!rows.length"><td :colspan="selectedFields.length + (readonly ? 4 : 5)" class="monthly-task-empty">暂无月度计划</td></tr>
    </tbody></table></div><PaginationBar :page="page" :page-size="pageSize" :total="rows.length" :total-pages="totalPages" @change="page = $event" /></template>
  </FullscreenPanel>
  <MonthlyPlanFieldDialog v-model="selected" :open="columnsOpen" :fields="availableFields" @close="columnsOpen = false" />
  <TaskQuickFillDialog :open="quickFillOpen" monthly :templates="humanResourcesMonthlyTaskTemplates" @close="quickFillOpen = false" @confirm="add" />
  <TaskTextFieldDialog :open="Boolean(editing)" :title="title" :value="editing?.task[editing.field] || ''" :templates="humanResourcesMonthlyTaskTemplates" :max-length="editing?.field === 'scope_name' ? 255 : editing?.field === 'work_content' ? 10000 : undefined" :template-field="editing?.field === 'scope_name' ? 'dimension' : editing?.field === 'work_task' ? 'task_name' : 'work_content'" @close="editing = null" @save="saveText" />
</template>
<style scoped src="./MonthlyPlanPanel.css"></style>
