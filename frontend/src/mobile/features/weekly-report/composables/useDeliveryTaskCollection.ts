import { mobileStorage as localStorage } from "@/mobile/shared/storage"
import { computed, nextTick, onMounted, ref, watch } from "vue"

import { type ExamplePreviewField } from "@/mobile/components/feedback/ExamplePreviewButton.vue"
import { listUserOptions } from "@/mobile/features/directory/api"
import type { DirectoryUserOption } from "@/mobile/features/directory/types"
import {
  taskFieldDefinitions,
  emptyTask,
  type TaskColumn,
  type TaskDraft,
  type TaskFieldDefinition,
} from "@/mobile/features/weekly-report/task-draft"
import type { TaskTemplateOption } from "@/mobile/features/weekly-report/task-editing"
import { expandTemplateTasks } from "../task-groups"

export interface DeliveryTaskCollectionProps {

  title: string
  mode: "monthly" | "weekly"
  tasks: TaskDraft[]
  defaultOwnerId?: string; ownerName?: string
  /** 后端按角色返回的列配置；未返回时使用 Excel 顺序的内置配置。 */
  fieldDefinitions?: TaskFieldDefinition[]
  /** 客户是交付专员模板专属字段；职能组模板不展示客户列。 */
  includeCustomer?: boolean
  sampleContent?: string
  sampleFields?: ReadonlyArray<ExamplePreviewField>
  templates?: readonly TaskTemplateOption[]
  taskFactory?: (ownerName?: string) => TaskDraft
  reportId?: string
  /** 不同周报模板使用独立的列偏好，避免共用组件时互相覆盖。 */
  columnPreferenceKey?: string
}

export function useTaskCollection(props: DeliveryTaskCollectionProps, emit: (event: "update:tasks", tasks: TaskDraft[]) => void) {
  const createTask = (ownerName?: string) => (props.taskFactory || emptyTask)(ownerName)
  const templates = computed(() => props.templates || [])
  const quickFillOpen = ref(false)
  const columnsOpen = ref(false)
  const users = ref<DirectoryUserOption[]>([])
  const customerFilter = ref("")
  const plannedDateFilter = ref("")
  const taskPage = ref(1)
  const taskPageSize = 10
  const insertedTaskKeys = ref(new Set<string>())
  const monthlyColumns: TaskColumn[] = ["customer_name", "task_name", "work_content", "planned_completion_date", "owner_name"]
  const weeklyFallbackColumns: TaskColumn[] = [
    "output_description",
    "planned_completion_date",
    "progress_percent",
    "on_time_status",
  ]
  const selectedColumns = ref<TaskColumn[]>([])
  const showCustomer = computed(() => props.includeCustomer)
  const editableDelivery = computed(() => props.includeCustomer && ["delivery_specialist_v1", "delivery_assistant_v1"].includes(props.columnPreferenceKey || "") && props.mode === "weekly")
  const columnStorageKey = computed(
    () => `weekly-report:visible-columns:${props.columnPreferenceKey}:${props.mode}${editableDelivery.value ? ":all-fields-v2" : props.columnPreferenceKey === "functional_group_v1" ? ":all-fields-v3" : ""}`,
  )

  const customerOptions = computed(() =>
    Array.from(
      new Set(props.tasks.map((task) => task.customer_name.trim()).filter(name => name || editableDelivery.value)),
    ).sort((left, right) => left.localeCompare(right, "zh-CN")),
  )

  const filteredTaskEntries = computed(() =>
    props.tasks
      .map((task, index) => ({ task, index }))
      .filter(({ task }) =>
        insertedTaskKeys.value.has(task.client_key) || (
          (editableDelivery.value ? task.customer_name === customerFilter.value : !customerFilter.value || task.customer_name === customerFilter.value) &&
          (!plannedDateFilter.value || task.planned_completion_date === plannedDateFilter.value)
        ),
      )
      // 交付周任务保持保存顺序；其他模板沿用原客户归组方式。
      .sort((left, right) => {
        if (editableDelivery.value || !showCustomer.value) return left.index - right.index
        const customerOrder = left.task.customer_name.localeCompare(
          right.task.customer_name,
          "zh-CN",
        )
        return customerOrder || left.index - right.index
      }),
  )

  const totalTaskPages = computed(() => Math.ceil(filteredTaskEntries.value.length / taskPageSize))

  const pagedTaskEntries = computed(() => {
    return filteredTaskEntries.value.slice(0, taskPage.value * taskPageSize)
  })

  const availableFields = computed<TaskFieldDefinition[]>(() => {
    const source = props.fieldDefinitions?.length
      ? props.fieldDefinitions
      : taskFieldDefinitions
    const monthlyAllowed = new Set(monthlyColumns)
    const fields = source
      // 客户和工作任务始终是固定列，不进入“选择展示字段”。
      .filter((field) => !["customer_name", "task_name"].includes(field.code))
      .filter((field) => props.mode === "weekly" || monthlyAllowed.has(field.code))
      .sort((left, right) => left.sort_order - right.sort_order)
    if (fields.length) return fields
    const fallback = props.mode === "monthly" ? monthlyColumns : weeklyFallbackColumns
    return taskFieldDefinitions.filter(
      (field) =>
        !["customer_name", "task_name"].includes(field.code) && fallback.includes(field.code),
    )
  })

  const selectedFields = computed(() => {
    const selected = new Set(selectedColumns.value)
    return availableFields.value.filter((field) => selected.has(field.code))
  })

  function defaultColumns(fields: TaskFieldDefinition[]) {
    if (editableDelivery.value || props.columnPreferenceKey === "functional_group_v1") return fields.map(field => field.code)
    const defaults = fields
      .filter((field) => props.mode === "monthly" ? monthlyColumns.includes(field.code) : field.default_visible)
      .map((field) => field.code)
    if (defaults.length) return defaults
    const fallback = props.mode === "monthly" ? monthlyColumns : weeklyFallbackColumns
    return fields.filter((field) => fallback.includes(field.code)).map((field) => field.code)
  }

  function loadStoredColumns(fields: TaskFieldDefinition[]) {
    const availableCodes = new Set(fields.map((field) => field.code))
    try {
      const storedValue = localStorage.getItem(columnStorageKey.value)
      if (storedValue !== null) {
        const parsed = JSON.parse(storedValue)
        if (Array.isArray(parsed)) {
          return parsed.filter(
            (code): code is TaskColumn =>
              typeof code === "string" && availableCodes.has(code as TaskColumn),
          )
        }
      }
    } catch {
      localStorage.removeItem(columnStorageKey.value)
    }
    return defaultColumns(fields)
  }

  watch([availableFields, columnStorageKey], ([fields]) => {
    // 优先恢复当前模板的本地偏好；字段配置变化后自动清理已经失效的字段。
    selectedColumns.value = loadStoredColumns(fields)
  }, { immediate: true, deep: true })

  watch(selectedColumns, (columns) => {
    localStorage.setItem(columnStorageKey.value, JSON.stringify(columns))
  }, { deep: true })

  watch([customerFilter, plannedDateFilter], () => {
    taskPage.value = 1
  })
  watch([customerFilter, plannedDateFilter], () => { insertedTaskKeys.value.clear() })

  watch(customerOptions, (options) => {
    if (editableDelivery.value && !options.includes(customerFilter.value)) customerFilter.value = options[0] || ""
    else if (customerFilter.value && !options.includes(customerFilter.value)) customerFilter.value = ""
  }, { immediate: true })

  watch(totalTaskPages, (total) => {
    taskPage.value = total ? Math.min(taskPage.value, total) : 1
  }, { immediate: true })

  async function loadUsers() {
    try {
      users.value = (await listUserOptions()).items
    } catch {
      // 用户选项接口不可用时仍允许保存文本值，不阻断周报填写。
      users.value = []
    }
  }

  function addTask() { quickFillOpen.value = true }

  function addTemplates(customer: string, indexes: number[]) {
    const tasks = indexes.flatMap(index => expandTemplateTasks(() => ({ ...createTask(props.ownerName), customer_name: customer, task_source: "template" as const, task_template: templates.value[index]!.task, task_values: Array(templates.value[index]!.task.split(/[?？]/).length - 1).fill(""), task_name: templates.value[index]!.task, work_content: templates.value[index]!.work, owner_id: props.defaultOwnerId || null, updated_at: currentLocalTimestamp() })))
    customerFilter.value = customer
    plannedDateFilter.value = ""
    if (availableFields.value.some(field => field.code === "work_content") && !selectedColumns.value.includes("work_content")) selectedColumns.value.push("work_content")
    emit("update:tasks", [...props.tasks, ...tasks])
    quickFillOpen.value = false
  }

  function currentLocalTimestamp() {
    const value = new Date()
    const pad = (part: number) => String(part).padStart(2, "0")
    return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}T${pad(value.getHours())}:${pad(value.getMinutes())}:${pad(value.getSeconds())}`
  }

  function assignCustomer(customer: string) {
    if (!customer.trim()) return
    emit("update:tasks", props.tasks.map(task => !task.customer_name.trim()
      ? { ...task, customer_name: customer, updated_at: currentLocalTimestamp() } : task))
    customerFilter.value = customer
  }

  function removeTask(index: number) {
    emit("update:tasks", props.tasks.filter((_, itemIndex) => itemIndex !== index))
  }

  function patchTask(key: string, value: Partial<TaskDraft>) {
    const original = props.tasks.find(task => task.client_key === key)
    if (!original) return
    emit("update:tasks", props.tasks.map(task => {
      const patch: Partial<TaskDraft> = task.client_key === key ? { ...value } : {}
      if ((task.task_text_id || task.task_group_key || task.client_key) === (original.task_text_id || original.task_group_key || original.client_key)) {
        for (const field of ["task_name", "task_source", "task_template", "task_values"] as const) {
          if (field in value) Object.assign(patch, { [field]: value[field] })
        }
      }
      if ((task.work_content_text_id || task.work_content_group_key || task.client_key) === (original.work_content_text_id || original.work_content_group_key || original.client_key) && "work_content" in value) patch.work_content = value.work_content
      if (task.client_key === key && task.quality_percent !== undefined && ("progress_percent" in value || "quality_percent" in value)) {
        patch.completion_rate = Math.round((Number(value.progress_percent ?? task.progress_percent ?? 0) + Number(value.quality_percent ?? task.quality_percent ?? 0)) / 2)
      }
      return Object.keys(patch).length ? { ...task, ...patch, updated_at: currentLocalTimestamp() } : task
    }))
  }

  async function insertTask(index: number, shared?: "task_name" | "work_content") {
    const tasks = props.tasks.map(task => ({ ...task }))
    const task = { ...createTask(props.ownerName), owner_id: props.defaultOwnerId || null, updated_at: currentLocalTimestamp() }
    const origin = tasks[index]
    task.customer_name = origin?.customer_name || customerFilter.value
    if (origin && shared) {
      origin.task_group_key ||= origin.task_text_id || origin.client_key
      origin.work_content_group_key ||= origin.work_content_text_id || origin.client_key
      Object.assign(task, { task_text_id: origin.task_text_id, task_group_key: origin.task_group_key, task_name: origin.task_name, task_source: origin.task_source, task_template: origin.task_template, task_values: [...(origin.task_values || [])] })
      if (shared === "work_content") Object.assign(task, { work_content_text_id: origin.work_content_text_id, work_content_group_key: origin.work_content_group_key, work_content: origin.work_content })
    }
    let after = index + 1
    if (origin && shared) {
      const group = shared === "task_name" ? "task_group_key" : "work_content_group_key"
      while (after < tasks.length && tasks[after]?.[group] === origin[group]) after++
    }
    tasks.splice(after, 0, task)
    // 新空行暂时保留在筛选结果中，避免因客户或日期尚未填写而立即消失。
    insertedTaskKeys.value.add(task.client_key)
    if (!shared && index >= props.tasks.length) taskPage.value = Math.ceil((filteredTaskEntries.value.length + 1) / taskPageSize)
    emit("update:tasks", tasks)
    await nextTick()
    const position = filteredTaskEntries.value.findIndex(entry => entry.task.client_key === task.client_key)
    taskPage.value = Math.max(taskPage.value, Math.floor(Math.max(0, position) / taskPageSize) + 1)
  }

  function customerRowspan(index: number) {
    if (!showCustomer.value) return 1
    const entries = pagedTaskEntries.value
    const currentCustomer = entries[index]?.task.customer_name || ""
    if (index > 0 && (entries[index - 1]?.task.customer_name || "") === currentCustomer) return 0
    let rowspan = 1
    while (entries[index + rowspan]?.task.customer_name === currentCustomer) rowspan += 1
    return rowspan
  }

  function displayValue(task: TaskDraft, column: TaskColumn) {
    if (column === "customer_name") return task.customer_name || "未填写"
    if (["progress_percent", "quality_percent", "completion_rate"].includes(column)) return `${Math.round(Number(task.progress_percent ?? 0))}%`
    if (column === "on_time_status") return ({ pending: "待完成", in_progress: "进行中", on_time: "按时完成", late: "延期完成", overdue: "逾期未完成", completed: "已完成", not_applicable: "不适用" })[task[column]] || "—"
    return String(task[column] || "—")
  }

  onMounted(() => void loadUsers())

  return { assignCustomer, addTemplates, filteredTaskEntries, quickFillOpen, columnsOpen, users, customerFilter, plannedDateFilter, taskPage, taskPageSize, showCustomer, editableDelivery, customerOptions, selectedColumns, availableFields, selectedFields, totalTaskPages, pagedTaskEntries, addTask, removeTask, patchTask, insertTask, customerRowspan, displayValue }
}

