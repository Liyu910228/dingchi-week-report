import { moveDailyTasks } from "@/features/weekly-report/period"
import { taskTextMetadata, loadedTaskTextMetadata } from "@/features/weekly-report/task-texts"
import { useUnsavedChanges } from "@/shared/forms/useUnsavedChanges"
import { computed, reactive, ref, watch } from "vue"

import { useAuthStore } from "@/features/auth/store"
import { useMonthlyPlanTasks } from "../monthly-plan/useMonthlyPlanTasks"
import {
  createReport,

  getReportDetail,
  getReportTemplate,

  updateReport,
} from "../api"
import type {
  DailyWorkTask,
  ReportAttachment,
  ReportItem,
  ReportPayload,
  ReportTemplateField,
  WeeklyReportDetail,
} from "../types"
import {
  functionalTaskFieldDefinitions,
  emptyFunctionalTask,
  type FunctionalTaskDraft,
  type FunctionalTaskFieldDefinition,
} from "./types"

function isoDate(value: Date) {
  const month = String(value.getMonth() + 1).padStart(2, "0")
  const day = String(value.getDate()).padStart(2, "0")
  return `${value.getFullYear()}-${month}-${day}`
}

function currentMonday() {
  const value = new Date()
  const day = value.getDay() || 7
  value.setDate(value.getDate() - day + 1)
  return isoDate(value)
}

function endOfWeek(start: string) {
  const value = new Date(`${start}T00:00:00`)
  value.setDate(value.getDate() + 6)
  return isoDate(value)
}

function taskCode(task: Pick<FunctionalTaskDraft, "client_key">, prefix = "delivery") {
  return `${prefix}_${task.client_key}`.slice(0, 64)
}

export function hydrateReportItem(
  item: ReportItem,
  attachments: ReportAttachment[] = [],
): FunctionalTaskDraft {
  return {
    ...emptyFunctionalTask(item.owner_name_snapshot),
    client_key: item.id || item.task_code,
    updated_at: item.updated_at,
    customer_name: item.customer_name_snapshot,
    ...loadedTaskTextMetadata(item),
    task_name: item.task_name_snapshot,
    work_content: item.work_content,
    output_description: item.output_description,
    planned_completion_date: item.planned_completion_date || "",
    progress_text: item.progress_text,
    progress_percent: item.progress_percent ?? 0,
    delay_reason: item.delay_reason,
    on_time_status: item.on_time_status,
    actual_completion_date: item.actual_completion_date || "",
    owner_id: item.owner_id,
    owner_name: item.owner_name_snapshot,
    collaborator_names: item.collaborator_names,
    document_links: item.document_links,
    attachments: attachments.map((attachment) => ({
      id: attachment.id,
      attachment_type: "attachment_type" in attachment ? attachment.attachment_type : "weekly_report",
      storage_key: "storage_key" in attachment ? attachment.storage_key : undefined,
      file_url: attachment.file_url,
      file_name: attachment.file_name,
      mime_type: "mime_type" in attachment ? attachment.mime_type : undefined,
      file_size: "file_size" in attachment ? attachment.file_size : undefined,
      description: attachment.description || "",
    })),
  }
}

function normalizeTaskFields(
  fields: ReportTemplateField[] | undefined,
  fallbackFields: FunctionalTaskFieldDefinition[],
): FunctionalTaskFieldDefinition[] {
  const known = new Set(fallbackFields.map((field) => field.code))
  const normalized = (fields || [])
    .filter((field) => known.has(field.field_code as FunctionalTaskFieldDefinition["code"]))
    .map((field) => ({
      code: field.field_code as FunctionalTaskFieldDefinition["code"],
      label: field.label,
      sort_order: Number(field.sort_order),
      default_visible: field.default_visible,
    }))
    .filter((field) => field.label && Number.isFinite(field.sort_order))
  return normalized.length ? normalized : fallbackFields
}

export interface FunctionalReportFormOptions {
  templateCode?: string
  includeCustomer?: boolean
  fallbackFields?: FunctionalTaskFieldDefinition[]
  taskCodePrefix?: string
}

export function useFunctionalReportForm(
  reportId: () => string,
  options: FunctionalReportFormOptions = {},
) {
  const templateCode = options.templateCode || "functional_group_v1"
  const includeCustomer = options.includeCustomer ?? false
  const fallbackFields = options.fallbackFields || functionalTaskFieldDefinitions
  const taskCodePrefix = options.taskCodePrefix || "functional"
  const authStore = useAuthStore()
  const start = currentMonday()
  const report = reactive({
    id: reportId(),
    month_key: start.slice(0, 7), period_start: start,
    period_end: endOfWeek(start),
    summary: "",
  })
  const monthlyTasksState = useMonthlyPlanTasks()
  const monthlySummary = ref("")
  const weeklyTasks = ref<FunctionalTaskDraft[]>([])
  const dailyTasks = ref<DailyWorkTask[]>([])
  const taskFields = ref<FunctionalTaskFieldDefinition[]>(fallbackFields)
  const isLoading = ref(true)
  const isSaving = ref(false)
  const errorMessage = ref("")
  const unsavedChanges = useUnsavedChanges(() => ({
    period_start: report.period_start, period_end: report.period_end,
    month_key: report.month_key, summary: report.summary,
    weeklyTasks: weeklyTasks.value, dailyTasks: reportId() ? [] : dailyTasks.value,
  }), () => !isLoading.value)

  const monthKey = computed(() => report.month_key)
  const isNew = computed(() => !reportId())
  let initialized = false

  function setPeriodStart(value: string) {
    dailyTasks.value = moveDailyTasks(dailyTasks.value, report.period_start, value)
    report.month_key = value.slice(0, 7)
    report.period_start = value
    report.period_end = endOfWeek(value)
  }

  async function loadMonthlyPlan() {
    await monthlyTasksState.load(monthKey.value)
    monthlySummary.value = monthlyTasksState.summary.value

  }

  async function loadTaskFields() {
    try {
      const template = await getReportTemplate(templateCode)
      taskFields.value = normalizeTaskFields(template.fields, fallbackFields)
    } catch {
      // 字段字典尚未初始化时使用内置 Excel 顺序，不影响周报填写。
      taskFields.value = fallbackFields
    }
  }

  async function load() {
    isLoading.value = true
    errorMessage.value = ""
    try {
      await loadTaskFields()
      if (reportId()) {
        const detail = await getReportDetail(reportId())
        Object.assign(report, {
          id: detail.report.id,
          month_key: detail.report.month_key, period_start: detail.report.period_start,
          period_end: detail.report.period_end,
          summary: detail.report.summary || "",
        })
        await monthlyTasksState.load(monthKey.value)
        monthlySummary.value = monthlyTasksState.summary.value

        const attachments = detail.attachments || []
        weeklyTasks.value = detail.items.map((item) =>
          hydrateReportItem(
            item,
            attachments.filter((attachment) => attachment.relation_sub_id === item.id),
          ),
        )
        dailyTasks.value = detail.daily_tasks || []
      } else {
        report.id = ""
        dailyTasks.value = []
        await loadMonthlyPlan()
      }
      initialized = true
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : "周报加载失败。"
    } finally {
      isLoading.value = false
    }
  }

  function buildPayload(): ReportPayload {
    return {
      period_start: report.period_start,
      period_end: report.period_end,
      summary: report.summary,
      risk_level: "none",
      risk_blocked: false,
      risk_reason: "",
      next_action: "",
      support_needed: "",
      expected_resolve_date: null,
      items: weeklyTasks.value.map((item, index) => ({
        task_code: taskCode(item, taskCodePrefix),
        section_code: "weekly_tasks",
        scope_type: includeCustomer ? "customer" : "overall",
        customer_name_snapshot: includeCustomer ? item.customer_name.trim() : "",
        ...taskTextMetadata(item),
        task_name_snapshot: item.task_name.trim(),
        work_content: item.work_content,
        output_description: item.output_description,
        planned_completion_date: item.planned_completion_date || null,
        progress_text: item.progress_text,
        progress_percent: item.progress_percent,
        delay_reason: item.delay_reason,
        on_time_status: item.on_time_status,
        actual_completion_date: item.actual_completion_date || null,
        owner_id: item.owner_id,
        owner_name_snapshot: item.owner_name,
        collaborator_names: item.collaborator_names,
        document_links: item.document_links,
        sort_order: index,
      })),
      metrics: [],
      daily_tasks: dailyTasks.value.map((task) => ({
        id: task.id.startsWith("draft-") ? undefined : task.id,
        work_date: task.work_date,
        work_content: task.work_content,
      })),
      attachments: weeklyTasks.value.flatMap((item) =>
        item.attachments
          .filter((attachment) => Boolean(attachment.id))
          .map((attachment) => ({
            id: attachment.id as string,
            task_code: taskCode(item, taskCodePrefix),
            description: attachment.description,
          })),
      ),
    }
  }

  async function save() {
    const savingSnapshot = unsavedChanges.snapshot()
    isSaving.value = true
    errorMessage.value = ""
    try {
      if (!monthlyTasksState.approved.value) throw new Error("请先完成所属月度的月度计划审批。")
      const detail = reportId()
        ? await updateReport(reportId(), buildPayload())
        : await createReport(buildPayload())
      report.id = detail.report.id
      unsavedChanges.markSaved(savingSnapshot)
      return detail.report.id
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : "保存周报失败。"
      return ""
    } finally {
      isSaving.value = false
    }
  }

  watch(() => report.period_start, async () => {
    if (initialized) await loadMonthlyPlan()
  })

  return {
    buildPayload, unsavedChanges, monthlyTasksState,
    report, monthlySummary, weeklyTasks, dailyTasks, taskFields, monthKey, isNew,
    isLoading, isSaving, errorMessage, authStore, setPeriodStart, load, save, }
}
