import type { TaskTextMetadata } from "@/mobile/features/weekly-report/task-texts"
/** 交付助理周报任务；字段顺序与 Excel 模板一致。 */
export interface DeliveryAssistantTaskDraft extends TaskTextMetadata {
  client_key: string
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
  attachments: DeliveryAssistantTaskAttachment[]
}

export interface DeliveryAssistantTaskAttachment {
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

export type DeliveryAssistantTaskColumn = keyof Pick<
  DeliveryAssistantTaskDraft,
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

export interface DeliveryAssistantTaskFieldDefinition {
  code: DeliveryAssistantTaskColumn
  label: string
  sort_order: number
  default_visible: boolean
}

/** 列顺序来自交付助理 Excel，列表允许通过字典覆盖。 */
export const deliveryAssistantTaskFieldDefinitions: DeliveryAssistantTaskFieldDefinition[] = [
  { code: "customer_name", label: "客户", sort_order: 1, default_visible: true },
  { code: "task_name", label: "工作任务", sort_order: 2, default_visible: true },
  { code: "work_content", label: "主要工作内容", sort_order: 3, default_visible: true },
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

export const deliveryAssistantColumnLabels: Record<DeliveryAssistantTaskColumn, string> =
  deliveryAssistantTaskFieldDefinitions.reduce((labels, field) => {
    labels[field.code] = field.label
    return labels
  }, {} as Record<DeliveryAssistantTaskColumn, string>)

export function emptyDeliveryAssistantTask(ownerName = ""): DeliveryAssistantTaskDraft {
  return {
    task_group_key: globalThis.crypto?.randomUUID?.() || `task-${Date.now()}-${Math.random()}`,
    work_content_group_key: globalThis.crypto?.randomUUID?.() || `work-${Date.now()}-${Math.random()}`,
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
