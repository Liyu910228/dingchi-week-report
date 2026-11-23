import type { TaskTextMetadata } from "@/features/weekly-report/task-texts"
/** ITO 销售 v1 周报任务；字段顺序与《ITO销售周报模板》一致。 */
export interface ItoSalesTaskDraft extends TaskTextMetadata {
  client_key: string
  task_code?: string
  updated_at?: string
  customer_name: string
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
  attachments: ItoSalesTaskAttachment[]
}

export interface ItoSalesTaskAttachment {
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

export type ItoSalesTaskColumn = keyof Pick<
  ItoSalesTaskDraft,
  | "customer_name"
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

export interface ItoSalesTaskFieldDefinition {
  code: ItoSalesTaskColumn
  label: string
  sort_order: number
  default_visible: boolean
}

/** 列定义来自 Excel；列表展示顺序还可由 system_dictionary 覆盖。 */
export const itoSalesTaskFieldDefinitions: ItoSalesTaskFieldDefinition[] = [
  { code: "customer_name", label: "维度", sort_order: 1, default_visible: true },
  { code: "task_name", label: "工作任务", sort_order: 2, default_visible: true },
  { code: "work_content", label: "主要工作指引", sort_order: 3, default_visible: true },
  { code: "output_description", label: "输出成果", sort_order: 4, default_visible: true },
  { code: "planned_completion_date", label: "计划完成时间", sort_order: 5, default_visible: true },
  { code: "progress_text", label: "工作进展（截至月日）", sort_order: 6, default_visible: true },
  { code: "progress_percent", label: "完成进度（百分比）", sort_order: 7, default_visible: true },
  { code: "quality_percent", label: "完成质量（百分比）", sort_order: 8, default_visible: true },
  { code: "completion_rate", label: "月度工作完成率（完成进度*50%+完成质量*50%）", sort_order: 9, default_visible: true },
  { code: "delay_reason", label: "进度缓慢原因说明", sort_order: 10, default_visible: true },
  { code: "on_time_status", label: "是否在计划时间内完成", sort_order: 11, default_visible: true },
  { code: "actual_completion_date", label: "实际完成时间", sort_order: 12, default_visible: true },
  { code: "owner_name", label: "责任人", sort_order: 13, default_visible: true },
  { code: "collaborator_names", label: "协作人", sort_order: 14, default_visible: true },
  { code: "document_links", label: "相关文档链接或佐证材料", sort_order: 15, default_visible: true },
]

export function emptyItoSalesTask(ownerName = ""): ItoSalesTaskDraft {
  return {
    client_key: globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`,
    customer_name: "",
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
