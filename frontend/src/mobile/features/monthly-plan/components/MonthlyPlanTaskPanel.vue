<script setup lang="ts">
import CustomerTabsHeader from "@/mobile/features/submissions/components/CustomerTabsHeader.vue"
import {inject} from "vue"
import {customerScopeKey} from "@/mobile/features/submissions/customer-scope"
const customerScope=inject(customerScopeKey,undefined)
import { taskPreviewLimitKey } from "@/mobile/shared/task-preview"
const previewLimit=inject(taskPreviewLimitKey,undefined)
import TaskHierarchy from "@/mobile/components/data-display/TaskHierarchy.vue"
import FullscreenPanel from "@/mobile/components/layout/FullscreenPanel.vue"
import MonthlyPlanFieldDialog from "./MonthlyPlanFieldDialog.vue"
import MonthlyPlanTaskCells from "./MonthlyPlanTaskCells.vue"
import { useMonthlyTaskFields } from "../useMonthlyTaskFields"
import { formatDateTime } from "@/utils/date"
import MonthlyPlanOutcomeCells from "./MonthlyPlanOutcomeCells.vue"
import { computed, defineAsyncComponent, ref, watch } from "vue"
import { isSupportedTemplate } from "@/mobile/features/weekly-report/template-support"
import { Plus } from "lucide-vue-next"
import ExamplePreviewButton from "@/mobile/components/feedback/ExamplePreviewButton.vue"
import { expandMonthlyTasks, patchMonthlyTasks, insertMonthlyChild, monthlyRowSpan, monthlyGroupKey, type MonthlyGroupLevel } from "../task-groups"
import { createId } from "@/utils/id"
import DeliveryQuickFillDialog from "@/mobile/features/weekly-report/components/TaskQuickFillDialog.vue"
import TemplateCustomerCell from "@/mobile/features/weekly-report/components/TemplateCustomerCell.vue"
import { monthlyPlanScopeLabel } from "@/mobile/features/weekly-report/monthly-plan/template-fields"
import { monthlyPlanSampleFields } from "@/mobile/features/weekly-report/monthly-plan/samples"
import type { MonthlyPlanTask, MonthlyPlanTaskPayload } from "@/mobile/features/weekly-report/monthly-plan/types"
import ScrollLoadMore from "@/mobile/components/navigation/ScrollLoadMore.vue"
import ScrollableTabs from "@/mobile/components/navigation/ScrollableTabs.vue"
import TemplateDimensionCell from "@/mobile/features/weekly-report/components/TemplateDimensionCell.vue"
import TemplateTaskCell from "@/mobile/features/weekly-report/components/TemplateTaskCell.vue"
import { previewTaskTemplate } from "@/mobile/features/weekly-report/task-texts"
import type { TaskTemplateOption, EditableTask } from "@/mobile/features/weekly-report/task-editing"
import TaskTextFieldDialog from "@/mobile/features/weekly-report/components/TaskTextFieldDialog.vue"
import { updateMonthlyTaskProgress } from "../api"
import { getErrorMessage } from "@/shared/api/errors"
const MonthlyPlanTaskDialog = defineAsyncComponent(() => import("./MonthlyPlanTaskDialog.vue"))
const props = defineProps<{
  templates?: readonly TaskTemplateOption[]
  tasks: MonthlyPlanTask[]
  monthKey: string
  templateCode?: string
  readonly?: boolean
  progressEditable?: boolean
  disabled?: boolean
  isLoading?: boolean
  errorMessage?: string
}>()
const emit = defineEmits<{ "update:tasks": [tasks: MonthlyPlanTask[]]; retry: [] }>()
const { users, columnsOpen, selected, availableFields, selectedFields, fieldError, reloadFields } = useMonthlyTaskFields(() => props.templateCode)
const dynamicTemplate = computed(() => isSupportedTemplate(props.templateCode))
const page = ref(1)
const pageSize = 10
const editorOpen = ref(false)
const quickFillOpen = ref(false)
const deliveryTemplate = computed(() => ["delivery_specialist_v1", "delivery_assistant_v1"].includes(props.templateCode || ""))
const recruitmentTemplate = computed(() => props.templateCode === "recruitment_v1")
const salesTemplate = computed(() => ["ito_sales_v1", "innovation_sales_v1"].includes(props.templateCode || ""))
const functionalTemplate = computed(() => props.templateCode === "functional_group_v1")
const editableTemplate = computed(() => deliveryTemplate.value || recruitmentTemplate.value || salesTemplate.value || functionalTemplate.value)
const taskTemplates = computed<readonly TaskTemplateOption[]>(() => props.templates || [])
const viewing = ref(false)
const selectedTask = ref<MonthlyPlanTask | null>(null)
const editingText = ref<MonthlyPlanTask | null>(null)
const editingField = ref<"scope_name" | "work_task" | "work_content">("work_task")
function openText(task: MonthlyPlanTask, field: "scope_name" | "work_task" | "work_content") {
  editingField.value = field
  editingText.value = task
}
const planTasks = computed(() => expandMonthlyTasks(props.tasks))
function insertChild(id: string, level: MonthlyGroupLevel) {
  if (unavailable.value || props.readonly) return
  const tasks = insertMonthlyChild(planTasks.value, id, level)
  const added = tasks.find(task => !planTasks.value.some(original => original.id === task.id))
  emit("update:tasks", tasks)
  if (added) page.value = Math.max(page.value, Math.floor(tasks.filter(task => !deliveryTemplate.value || task.scope_name === activeCustomer.value).findIndex(task => task.id === added.id) / pageSize) + 1)
}
const activeCustomer = ref("")
const customers = computed(() => [...new Set(planTasks.value.map(task => task.scope_name || ""))]
  .sort((a, b) => a.localeCompare(b, "zh-CN"))
  .map(id => ({ id, name: id || "未选择客户" })))
const filteredTasks = computed(() => deliveryTemplate.value
  ? planTasks.value.filter(task => (task.scope_name || "") === activeCustomer.value) : planTasks.value)
const totalPages = computed(() => Math.max(1, Math.ceil(filteredTasks.value.length / pageSize)))
const entries = computed(() => previewLimit?.value ? filteredTasks.value : filteredTasks.value.slice(0, page.value * pageSize))
watch(customers, tabs => {
  if (!tabs.some(tab => tab.id === activeCustomer.value)) activeCustomer.value = tabs[0]?.id || ""
}, { immediate: true })
watch(activeCustomer, () => { page.value = 1 })
function displayTask(task: MonthlyPlanTask) {
  return task.task_source === "template" && task.task_template
    ? previewTaskTemplate(task.task_template, task.task_values || []) : task.work_task
}
function patchTemplate(id: string, value: Partial<EditableTask>) {
  patch(id, { work_task: value.task_name, task_values: value.task_values })
}
const scopeLabel = computed(() => monthlyPlanScopeLabel(props.templateCode || ""))
const sampleFields = computed(() => monthlyPlanSampleFields(props.templateCode || ""))
const unavailable = computed(() => props.disabled || props.isLoading || Boolean(props.errorMessage) || progressBusy.value)
const progressBusy = ref(false)
const progressError = ref("")
const progressSaved = ref(false)
const liveProgressFields = new Set(["progress_text", "progress_percent", "quality_percent", "completion_rate", "delay_reason", "on_time_status", "actual_completion_date", "owner_id", "owner_name", "collaborator_names", "document_links"])
async function saveLiveProgress(id: string, fields: Partial<MonthlyPlanTask>) {
  const current = props.tasks.find(task => task.id === id)
  if (!current || !/^\d+$/.test(id) || Object.keys(fields).some(field => !liveProgressFields.has(field))) return
  progressBusy.value = true
  progressError.value = ""
  progressSaved.value = false
  try {
    const result = await updateMonthlyTaskProgress(id, { ...fields, revision: current.progress_revision || 0 })
    const updated = { ...current, ...result.values, progress_revision: result.revision, progress_updated_at: result.updated_at || null, progress_updated_by: result.updated_by || null, progress_updated_by_name: result.updated_by_name || "" }
    emit("update:tasks", props.tasks.map(task => task.id === id ? updated : task))
    progressSaved.value = true
  } catch (cause) {
    progressError.value = getErrorMessage(cause)
  } finally {
    progressBusy.value = false
  }
}
watch([planTasks, unavailable], ([tasks, blocked]) => {
  if (!props.readonly && !blocked && tasks.some((task, index) => task !== props.tasks[index])) emit("update:tasks", tasks)
}, { immediate: true })
watch([() => props.monthKey, () => props.isLoading], () => { editorOpen.value = false; editingText.value = null; quickFillOpen.value = false; page.value = 1 })
watch(totalPages, (total) => { page.value = Math.max(1, Math.min(page.value, total)) })
function open(task: MonthlyPlanTask | null, readonly = false) {
  selectedTask.value = task
  viewing.value = readonly
  editorOpen.value = true
}
function save(payload: MonthlyPlanTaskPayload, action: "close" | "next") {
  if (unavailable.value || props.readonly) return
  const tasks = [...props.tasks]
  const index = selectedTask.value ? tasks.findIndex((task) => task.id === selectedTask.value?.id) : -1
  const task = { ...(selectedTask.value || {}), id: selectedTask.value?.id || `draft-${createId()}`, ...payload }
  if (index >= 0) tasks.splice(index, 1, task)
  else tasks.push(task)
  emit("update:tasks", tasks)
  if (index < 0) page.value = Math.ceil(tasks.length / pageSize)
  if (action === "close") editorOpen.value = false
  else selectedTask.value = null
}
function patch(id: string, fields: Partial<MonthlyPlanTask>) {
  if (unavailable.value || (props.readonly && !props.progressEditable)) return
  const current = planTasks.value.find(task => task.id === id)
  if (current && ("progress_percent" in fields || "quality_percent" in fields)) fields.completion_rate = Math.round((Number(fields.progress_percent ?? current.progress_percent ?? 0) + Number(fields.quality_percent ?? current.quality_percent ?? 0)) / 2)
  if (props.readonly) {
    void saveLiveProgress(id, fields)
    return
  }
  emit("update:tasks", patchMonthlyTasks(planTasks.value, id, fields))
}
function saveText(value: string, templateIndex?: number) {
  if (editingText.value) {
    const current = props.tasks.find(task => task.id === editingText.value?.id)
    const template = templateIndex === undefined ? undefined : taskTemplates.value[templateIndex]
    const fields: Partial<MonthlyPlanTask> = { [editingField.value]: value }
    if (salesTemplate.value && template) {
      if (editingField.value === "scope_name" || !current?.scope_name?.trim()) Object.assign(fields, {
        scope_name: template.customer || "", customer_source: "template", customer_template: template.customer || "",
        customer_values: Array((template.customer || "").split(/[?？]/).length - 1).fill(""),
      })
      if (editingField.value === "work_task" || !current?.work_task.trim()) Object.assign(fields, {
        task_source: "template", task_template: template.task, work_task: template.task,
        task_values: Array(template.task.split(/[?？]/).length - 1).fill(""),
      })
    }
    if (recruitmentTemplate.value && template) {
      if (editingField.value === "scope_name" || !current?.scope_name?.trim()) Object.assign(fields, {
        scope_name: template.dimension || "", dimension_source: "template", dimension_template: template.dimension || "",
        dimension_values: Array((template.dimension || "").split(/[?？]/).length - 1).fill(""),
      })
      if (editingField.value === "work_task" || !current?.work_task.trim()) Object.assign(fields, {
        task_source: "template", task_template: template.task, work_task: template.task,
        task_values: Array(template.task.split(/[?？]/).length - 1).fill(""),
      })
    }
    if ((deliveryTemplate.value || functionalTemplate.value) && editingField.value === "work_task") {
      Object.assign(fields, template ? {
        task_source: "template", task_template: template.task,
        task_values: Array(template.task.split(/[?？]/).length - 1).fill(""), work_task: template.task,
      } : { task_source: "custom", task_template: "", task_values: [] })
    }
    if (template && editingField.value !== "work_content" && !current?.work_content?.trim()) fields.work_content = template.work
    patch(editingText.value.id, fields)
  }
  editingText.value = null
}
function addBlankTask() {
  if (unavailable.value || props.readonly) return
  const tasks = [...props.tasks]
  const index = tasks.length - 1
  tasks.splice(index + 1, 0, { id: `draft-${createId()}`, scope_name: deliveryTemplate.value ? activeCustomer.value : "", work_task: "", work_content: "", task_source: "custom" })
  emit("update:tasks", tasks)
  page.value = Math.max(page.value, Math.ceil((filteredTasks.value.length + 1) / pageSize))
}
function addPlans(customer: string, indexes: number[]) {
  if (unavailable.value || props.readonly) return
  const tasks = indexes.map(index => ({ id: `draft-${createId()}`, scope_name: salesTemplate.value ? taskTemplates.value[index]!.customer : recruitmentTemplate.value ? (taskTemplates.value[index]!.dimension || "") : customer, work_task: taskTemplates.value[index]!.task, work_content: taskTemplates.value[index]!.work,
    ...(editableTemplate.value ? { task_source: "template" as const, task_template: taskTemplates.value[index]!.task,
      task_values: Array(taskTemplates.value[index]!.task.split(/[?？]/).length - 1).fill("") } : {}),
    ...(salesTemplate.value ? { customer_source: "template" as const, customer_template: taskTemplates.value[index]!.customer || "", customer_values: Array((taskTemplates.value[index]!.customer || "").split(/[?？]/).length - 1).fill("") } : {}),
    ...(recruitmentTemplate.value ? { dimension_source: "template" as const, dimension_template: (taskTemplates.value[index]!.dimension || ""), dimension_values: Array((taskTemplates.value[index]!.dimension || "").split(/[?？]/).length - 1).fill("") } : {}) }))
  const expanded = expandMonthlyTasks([...planTasks.value, ...tasks])
  emit("update:tasks", expanded)
  quickFillOpen.value = false
  if (deliveryTemplate.value) activeCustomer.value = customer
}
</script>
<template>
  <FullscreenPanel v-if="readonly || isSupportedTemplate(templateCode)" title="月度计划" header-controls class="dashboard-card monthly-task-panel">
    <template #tabs><CustomerTabsHeader />
      <ScrollableTabs v-if="!customerScope?.enabled.value && deliveryTemplate && customers.length" v-model="activeCustomer" :items="customers" class="monthly-customer-tabs" />
    </template>
    <template #header-actions>
      <span v-if="readonly && progressEditable" class="live-progress-hint">右侧实时进度可直接保存</span>
      <button v-if="dynamicTemplate" class="ghost-button" type="button" @click="columnsOpen = true">展示字段</button>
    </template>
    <template #primary><button v-if="!readonly" class="primary-button" type="button" :disabled="unavailable" @click="editableTemplate ? quickFillOpen = true : open(null)">新增计划</button></template>
    <template #actions>
      <template v-if="!readonly">
        <ExamplePreviewButton content="" :fields="sampleFields" panel-title="月度计划填写样例" />
      </template>
    </template>
    <div v-if="isLoading" class="monthly-task-empty" aria-live="polite">正在加载月度计划…</div>
    <div v-else-if="errorMessage" class="monthly-task-empty" role="alert">
      <p>{{ errorMessage }}</p>
      <button class="ghost-button" type="button" :disabled="disabled" @click="emit('retry')">重试</button>
    </div>
    <template v-else>
      <p v-if="progressBusy" class="live-progress-message" aria-live="polite">正在保存实时进度…</p>
      <p v-else-if="progressError" class="live-progress-message error" role="alert">{{ progressError }}</p>
      <p v-else-if="progressSaved" class="live-progress-message success" aria-live="polite">实时进度已保存，计划基线和审批状态未改变。</p>
      <p v-if="dynamicTemplate && fieldError" role="alert">{{ fieldError }} <button type="button" class="ghost-button" @click="reloadFields">重试</button></p>
      <div class="monthly-task-table-wrap">
        <div class="mobile-task-cards">
            <TaskHierarchy :deletable="!readonly && !unavailable" :all-rows="planTasks" @remove="items => emit('update:tasks', planTasks.filter(row => !items.some(item => item.id === row.id)))" :rows="entries" :row-key="row => row.id" :task-key="row => monthlyGroupKey(row,'task')" :content-key="row => monthlyGroupKey(row,'content')" :title="row => displayTask(row)">
 <template #task="{row:task,index}">
              <div data-card-field :data-label="scopeLabel" v-if="scopeLabel && !deliveryTemplate" class="customer-name shared-monthly-cell"><template v-if="salesTemplate"><span v-if="readonly || unavailable" class="monthly-task-plain user-content">{{ task.customer_source === 'template' ? previewTaskTemplate(task.customer_template || '', task.customer_values || []) : task.scope_name || '—' }}</span><TemplateCustomerCell :label="scopeLabel" v-else-if="task.customer_source === 'template'" :task="{ ...task, customer_name: task.scope_name }" @patch="patch(task.id, { scope_name: $event.customer_name, customer_values: $event.customer_values })" /><button v-else class="monthly-task-text-cell user-content" type="button" :aria-label="`编辑${scopeLabel}`" @click="openText(task, 'scope_name')">{{ task.scope_name || `点击填写${scopeLabel}` }}</button></template><template v-else><TemplateDimensionCell v-if="recruitmentTemplate && !readonly && !unavailable && task.dimension_source === 'template'" :task="{ ...task, dimension: task.scope_name }" @patch="patch(task.id, { scope_name: $event.dimension, dimension_values: $event.dimension_values })" /><span v-else-if="recruitmentTemplate && (readonly || unavailable)" class="monthly-task-plain user-content">{{ task.dimension_source === 'template' ? previewTaskTemplate(task.dimension_template || '', task.dimension_values || []) : task.scope_name || '—' }}</span><button v-else-if="recruitmentTemplate && !readonly" class="monthly-task-text-cell user-content" type="button" :disabled="unavailable" aria-label="编辑维度" @click="openText(task, 'scope_name')">{{ task.scope_name || '点击填写维度' }}</button><template v-else>{{ task.scope_name || "—" }}</template></template><button data-task-tip="新增工作任务" aria-label="新增工作任务" v-if="!readonly && !unavailable" class="cell-insert" type="button" @click="insertChild(task.id, 'scope')"><Plus :size="16" /><span>新增工作任务</span></button></div>
              <div data-card-field data-label="工作任务"  class="shared-monthly-cell">
                <template v-if="editableTemplate">
                  <span v-if="readonly || unavailable" class="monthly-task-plain user-content">{{ displayTask(task) || "—" }}</span>
                  <TemplateTaskCell v-else-if="task.task_source === 'template' && task.task_template"
                    :task="{ task_name: task.work_task, task_template: task.task_template, task_values: task.task_values }"
                    @patch="patchTemplate(task.id, $event)" />
                  <button v-else class="monthly-task-text-cell user-content" type="button" @click="openText(task, 'work_task')">{{ task.work_task || "点击填写工作任务" }}</button>
                </template>
                <button v-else :class="editableTemplate && !readonly ? 'monthly-task-text-cell' : 'monthly-task-link'" type="button" :disabled="unavailable" @click="editableTemplate && !readonly ? openText(task, 'work_task') : open(task, true)">{{ task.work_task || "点击填写工作任务" }}</button>
                <button data-task-tip="新增工作内容" aria-label="新增工作内容" v-if="!readonly && !unavailable" class="cell-insert" type="button" @click="insertChild(task.id, 'task')"><Plus :size="16" /><span>新增工作内容</span></button>
              </div>
              </template>
 <template #content="{row:task,index}"><div data-card-field data-label="工作内容" v-if="!dynamicTemplate" class="shared-monthly-cell">
                <span v-if="readonly || unavailable" class="monthly-task-plain user-content">{{ task.work_content || "—" }}</span>
                <button v-else class="monthly-task-text-cell user-content" type="button" @click="openText(task, 'work_content')">{{ task.work_content || "点击填写工作内容" }}</button>
                <button data-task-tip="新增输出成果" aria-label="新增输出成果" v-if="!readonly && !unavailable" class="cell-insert" type="button" @click="insertChild(task.id, 'content')"><Plus :size="16" /><span>新增工作成果与进度</span></button>
              </div>
              <MonthlyPlanTaskCells v-if="dynamicTemplate" :task="task" :fields="selectedFields.filter(field => field.code === 'work_content')" :users="users" :readonly="readonly || unavailable" :progress-editable="Boolean(progressEditable) && !unavailable" :content-span="monthlyRowSpan(entries, index, 'content')" @patch="patch(task.id, $event)" @insert-content="insertChild(task.id, 'content')" /></template>
 <template #row="{row:task,index}"><MonthlyPlanTaskCells v-if="dynamicTemplate" :task="task" :fields="selectedFields.filter(field => field.code !== 'work_content')" :users="users" :readonly="readonly || unavailable" :progress-editable="Boolean(progressEditable) && !unavailable" :content-span="monthlyRowSpan(entries, index, 'content')" @patch="patch(task.id, $event)" @insert-content="insertChild(task.id, 'content')" />
              <div data-card-field data-label="更新时间" v-if="dynamicTemplate">{{ formatDateTime(task.progress_updated_at || task.updated_at) }}</div>
              <MonthlyPlanOutcomeCells v-else :task="task" :readonly="readonly || unavailable" @patch="patch(task.id, $event)" />
              <div data-card-field data-label="" v-if="!readonly" class="actions">
                <button v-if="!editableTemplate" class="link-button" type="button" :disabled="unavailable" @click="open(task, true)">查看</button>
                <button v-if="!editableTemplate" class="link-button" type="button" :disabled="unavailable" @click="open(task)">编辑</button>
              </div>
            </template>
</TaskHierarchy>
            <article data-mobile-task-card v-if="!filteredTasks.length"><div data-card-field :data-label="scopeLabel" :colspan="(dynamicTemplate ? selectedFields.length + 3 + (scopeLabel && !deliveryTemplate ? 1 : 0) : 5 + (scopeLabel ? 1 : 0)) + (readonly ? 0 : 1)" class="monthly-task-empty">{{ readonly ? "暂无月度计划" : "暂无月度计划，请新增计划" }}</div></article>
        </div>
      </div>
      <ScrollLoadMore v-if="!previewLimit" :show-end="false" :page="page" :page-size="pageSize" :total="filteredTasks.length" :total-pages="totalPages" @change="page = $event" />
      <div v-if="!readonly && editableTemplate" class="monthly-add-task"><button class="ghost-button" type="button" :disabled="unavailable" @click="addBlankTask"><Plus :size="18" aria-hidden="true" /><span>新增任务</span></button></div>
    </template>
  </FullscreenPanel>
  <MonthlyPlanFieldDialog v-model="selected" :open="dynamicTemplate && columnsOpen"  :error="fieldError" @retry="reloadFields" :fields="availableFields" @close="columnsOpen = false" />
  <MonthlyPlanTaskDialog :templates="taskTemplates" v-if="templateCode !== 'human_resources_v1' && !editableTemplate && (readonly || isSupportedTemplate(templateCode))" :template-code="templateCode" :open="editorOpen" :task="selectedTask" :readonly="viewing" @close="editorOpen = false" @save="save" />
  <TaskTextFieldDialog v-if="templateCode !== 'human_resources_v1' && isSupportedTemplate(templateCode)" :customer-label="scopeLabel" :open="Boolean(editingText)" :title="editingField === 'scope_name' ? scopeLabel : editingField === 'work_content' ? '工作内容' : '工作任务'" :value="editingText?.[editingField] || ''" :max-length="editingField === 'scope_name' ? 255 : editingField === 'work_content' ? 10000 : editableTemplate ? undefined : 2000" :template-field="editingField === 'scope_name' ? (salesTemplate ? 'customer_name' : 'dimension') : editingField === 'work_content' ? 'work_content' : 'task_name'" :templates="taskTemplates" @close="editingText = null" @save="saveText" />
  <DeliveryQuickFillDialog v-if="editableTemplate" :open="quickFillOpen" :customer-label="scopeLabel" monthly :scope-less="functionalTemplate" :sales="salesTemplate" :recruitment="recruitmentTemplate" :templates="taskTemplates" @close="quickFillOpen = false" @confirm="addPlans" />
</template>
<style scoped src="./MonthlyPlanTaskPanel.css"></style>
<style scoped src="@/mobile/components/data-display/TaskCards.css"></style>
