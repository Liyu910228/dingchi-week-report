import { previewTaskTemplate } from "./task-texts"
import { formatDateTime } from "@/utils/date"
import type { ReportItem, ReportTemplateField } from "./types"

/**
 * 周报查看页可选的任务字段。
 *
 * 角色模板接口会优先返回字典配置；当接口暂时没有返回字段配置时，使用
 * 这份公共兜底定义，保证查看页仍能展示完整的任务信息。
 */
export const defaultReportTaskFields: ReportTemplateField[] = [
  { field_code: "customer_name", label: "客户", sort_order: 1, default_visible: true },
  { field_code: "task_name", label: "工作任务", sort_order: 2, default_visible: true },
  { field_code: "work_content", label: "主要工作内容", sort_order: 3, default_visible: false },
  { field_code: "output_description", label: "输出成果", sort_order: 4, default_visible: false },
  { field_code: "planned_completion_date", label: "计划完成时间", sort_order: 5, default_visible: false },
  { field_code: "progress_text", label: "工作进展（截至月日）", sort_order: 6, default_visible: false },
  { field_code: "progress_percent", label: "完成进度（百分比）", sort_order: 7, default_visible: false },
  { field_code: "quality_percent", label: "完成质量（百分比）", sort_order: 8, default_visible: false },
  { field_code: "completion_rate", label: "月度工作完成率（完成进度*50%+完成质量*50%）", sort_order: 9, default_visible: false },
  { field_code: "delay_reason", label: "进度缓慢原因说明", sort_order: 10, default_visible: false },
  { field_code: "on_time_status", label: "是否在计划时间内完成", sort_order: 11, default_visible: false },
  { field_code: "actual_completion_date", label: "实际完成时间", sort_order: 12, default_visible: false },
  { field_code: "owner_name", label: "责任人", sort_order: 13, default_visible: false },
  { field_code: "collaborator_names", label: "协作人", sort_order: 14, default_visible: false },
  { field_code: "document_links", label: "相关文档链接或佐证材料", sort_order: 15, default_visible: false },
]

/** 招聘模板用“维度”作为任务主字段，交付/销售模板使用“客户”。 */
export const defaultRecruitmentTaskFields: ReportTemplateField[] = [
  { field_code: "dimension", label: "维度", sort_order: 1, default_visible: true },
  { field_code: "task_name", label: "工作任务", sort_order: 2, default_visible: true },
  { field_code: "work_content", label: "主要工作内容", sort_order: 3, default_visible: true },
  { field_code: "output_description", label: "输出成果", sort_order: 4, default_visible: true },
  { field_code: "planned_completion_date", label: "计划完成时间", sort_order: 5, default_visible: true },
  { field_code: "progress_text", label: "工作进展（截至月日）", sort_order: 6, default_visible: true },
  { field_code: "progress_percent", label: "完成进度（百分比）", sort_order: 7, default_visible: true },
  { field_code: "quality_percent", label: "完成质量（百分比）", sort_order: 8, default_visible: true },
  { field_code: "completion_rate", label: "月度工作完成率（完成进度*50%+完成质量*50%）", sort_order: 9, default_visible: true },
  { field_code: "delay_reason", label: "进度缓慢原因说明", sort_order: 10, default_visible: true },
  { field_code: "on_time_status", label: "是否在计划时间内完成", sort_order: 11, default_visible: true },
  { field_code: "actual_completion_date", label: "实际完成时间", sort_order: 12, default_visible: true },
  { field_code: "owner_name", label: "责任人", sort_order: 13, default_visible: true },
  { field_code: "collaborator_names", label: "协作人", sort_order: 14, default_visible: true },
  { field_code: "document_links", label: "相关文档链接或佐证材料", sort_order: 15, default_visible: true },
]

// 查看页固定展示主字段、工作任务、状态和更新时间；这些字段不进入可选列。
const fixedFieldCodes = new Set([
  "customer_name",
  "dimension",
  "task_name",
  "on_time_status",
  "updated_at",
])

export function normalizeReportTaskFields(fields?: ReportTemplateField[] | null): ReportTemplateField[] {
  const source = fields?.length ? fields : defaultReportTaskFields
  return [...source]
    .filter((field) => !fixedFieldCodes.has(field.field_code))
    .sort((left, right) => left.sort_order - right.sort_order)
}

export function allReportTaskFields(fields?: ReportTemplateField[] | null): ReportTemplateField[] {
  const source = fields?.length ? fields : defaultReportTaskFields
  return [...source].sort((left, right) => left.sort_order - right.sort_order)
}

export function reportTaskStatusLabel(value: string | null | undefined): string {
  return ({
    pending: "待完成",
    completed: "已完成",
    in_progress: "进行中",
    on_time: "按时完成",
    late: "延期完成",
    overdue: "逾期未完成",
    not_applicable: "不适用",
  } as Record<string, string>)[value || ""] || "—"
}

export function formatReportTaskField(item: ReportItem, fieldCode: string): string {
  if (fieldCode === "customer_name" && item.customer_source === "template" && item.customer_template) return previewTaskTemplate(item.customer_template, item.customer_values || [])
  if (fieldCode === "customer_name") return item.customer_name_snapshot || "—"
  if (fieldCode === "dimension") {
    if (item.dimension_source === "template" && item.dimension_template) return previewTaskTemplate(item.dimension_template, item.dimension_values || [])
    const dimensionLabels: Record<string, string> = {
      overall: "总体目标",
      demand: "需求管理",
      demand_management: "需求管理",
      other: "其他",
    }
    return dimensionLabels[item.section_code] || item.section_name_snapshot || item.section_code || "—"
  }
  if (fieldCode === "task_name") {
    if (item.task_source === "template" && item.task_template) {
      return previewTaskTemplate(item.task_template, item.task_values || [])
    }
    return item.task_name_snapshot || "—"
  }
  // API uses the persisted snapshot name while editable drafts call it owner_name.
  if (fieldCode === "owner_name") return item.owner_name_snapshot || "—"
  if (fieldCode === "on_time_status") {
    return reportTaskStatusLabel(item.on_time_status)
  }
  if (fieldCode === "progress_percent" || fieldCode === "quality_percent" || fieldCode === "completion_rate") {
    const value = item[fieldCode as keyof ReportItem]
    return `${Math.round(Number(value ?? 0))}%`
  }
  if (fieldCode === "planned_completion_date" || fieldCode === "actual_completion_date") {
    const value = item[fieldCode as keyof ReportItem]
    return value ? formatDateTime(String(value)) : "—"
  }
  if (fieldCode === "updated_at" || fieldCode === "created_at") {
    const value = item[fieldCode as keyof ReportItem]
    return value ? formatDateTime(String(value)) : "—"
  }

  const value = item[fieldCode as keyof ReportItem]
  if (value === null || value === undefined || value === "") return "—"
  return String(value)
}

export function reportTaskUpdatedAt(item: ReportItem): string {
  return formatReportTaskField(item, "updated_at")
}
