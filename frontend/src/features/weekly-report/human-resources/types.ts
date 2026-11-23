import type { TaskTextMetadata } from "@/features/weekly-report/task-texts"
/** 人资专属周报任务；模块按 Excel 原文存放于 dimension，不读取客户配置。 */
export interface HumanResourcesTaskDraft extends TaskTextMetadata {
  client_key: string
  /** 已保存任务沿用后端 task_code；新增任务保存前为空。 */
  task_code?: string
  updated_at?: string
  dimension: string
  task_name: string
  work_content: string
  output_description: string
  planned_completion_date: string
  progress_text: string
  progress_percent: number | null
  quality_percent: number | null
  completion_rate: number | null
  delay_reason: string
  on_time_status: string
  actual_completion_date: string
  owner_id: string | null
  owner_name: string
  collaborator_names: string
  document_links: string
  attachments: HumanResourcesTaskAttachment[]
}

export interface HumanResourcesTaskAttachment {
  id?: string
  file?: File
  attachment_type?: string
  storage_key?: string
  file_url?: string
  file_name: string
  mime_type?: string
  file_size?: number
  description: string
}

export type HumanResourcesTaskColumn = keyof Pick<
  HumanResourcesTaskDraft,
  | "dimension"
  | "task_name"
  | "work_content"
  | "output_description"
  | "planned_completion_date"
  | "progress_text"
  | "progress_percent"
  | "quality_percent"
  | "completion_rate"
  | "delay_reason"
  | "on_time_status"
  | "actual_completion_date"
  | "owner_name"
  | "collaborator_names"
  | "document_links"
>

export interface HumanResourcesTaskFieldDefinition {
  code: HumanResourcesTaskColumn
  label: string
  sort_order: number
  default_visible: boolean
}

/** 字段顺序与人资周报 Excel 表头保持一致；列表可被模板字典覆盖。 */
export const humanResourcesTaskFieldDefinitions: HumanResourcesTaskFieldDefinition[] = [
  { code: "dimension", label: "模块", sort_order: 1, default_visible: true },
  { code: "task_name", label: "工作事项", sort_order: 2, default_visible: true },
  { code: "work_content", label: "主要工作内容", sort_order: 3, default_visible: true },
  { code: "output_description", label: "输出成果", sort_order: 4, default_visible: true },
  { code: "planned_completion_date", label: "计划完成时间", sort_order: 5, default_visible: true },
  { code: "progress_text", label: "工作进展", sort_order: 6, default_visible: true },
  { code: "progress_percent", label: "完成进度（百分比）", sort_order: 7, default_visible: true },
  { code: "delay_reason", label: "进度缓慢原因说明", sort_order: 10, default_visible: true },
  { code: "on_time_status", label: "是否在计划时间内完成", sort_order: 11, default_visible: true },
  { code: "actual_completion_date", label: "实际完成时间", sort_order: 12, default_visible: true },
  { code: "owner_name", label: "责任人", sort_order: 13, default_visible: true },
  { code: "collaborator_names", label: "协作人", sort_order: 14, default_visible: true },
  { code: "document_links", label: "相关文档链接或佐证材料", sort_order: 15, default_visible: true },
]

export function emptyHumanResourcesTask(ownerName = ""): HumanResourcesTaskDraft {
  return {
    client_key: globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`,
    dimension: "",
    task_name: "",
    work_content: "",
    output_description: "",
    planned_completion_date: "",
    progress_text: "",
    progress_percent: 0,
    quality_percent: 0,
    completion_rate: 0,
    delay_reason: "",
    on_time_status: "in_progress",
    actual_completion_date: "",
    owner_id: null,
    owner_name: ownerName,
    collaborator_names: "",
    document_links: "",
    attachments: [],
  }
}
