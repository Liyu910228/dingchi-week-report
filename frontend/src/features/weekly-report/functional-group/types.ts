import type { TaskTextMetadata } from "@/features/weekly-report/task-texts"
export interface FunctionalTaskDraft extends TaskTextMetadata {
  client_key: string
  /** 后端任务更新时间；新建任务在周报保存前使用本地时间展示。 */
  updated_at?: string
  customer_name: string
  task_name: string
  work_content: string
  output_description: string
  planned_completion_date: string
  progress_text: string
  progress_percent: number | null
  quality_percent?: number | null
  completion_rate?: number | null
  delay_reason: string
  on_time_status: string
  actual_completion_date: string
  owner_id: string | null
  owner_name: string
  collaborator_names: string
  document_links: string
  attachments: FunctionalTaskAttachment[]
}

/** 任务附件；新选择的文件暂存于浏览器，保存周报后由附件接口上传。 */
export interface FunctionalTaskAttachment {
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

export type FunctionalTaskColumn = keyof Pick<
  FunctionalTaskDraft,
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

/** 周报任务列表列定义；序号列由列表组件固定生成，不放入字典。 */
export interface FunctionalTaskFieldDefinition {
  code: FunctionalTaskColumn
  label: string
  sort_order: number
  default_visible: boolean
}

/** 与交付专员 Excel 模板一致的内置顺序，后端字典返回后可覆盖。 */
export const functionalTaskFieldDefinitions: FunctionalTaskFieldDefinition[] = [
  { code: "task_name", label: "工作任务", sort_order: 2, default_visible: true },
  { code: "work_content", label: "主要工作内容", sort_order: 3, default_visible: true },
  { code: "output_description", label: "输出成果", sort_order: 4, default_visible: true },
  { code: "planned_completion_date", label: "计划完成时间", sort_order: 5, default_visible: true },
  { code: "progress_text", label: "工作进展（截至月日）", sort_order: 6, default_visible: true },
  { code: "progress_percent", label: "完成进度（百分比）", sort_order: 7, default_visible: true },
  { code: "delay_reason", label: "进度缓慢原因说明", sort_order: 8, default_visible: true },
  { code: "on_time_status", label: "是否在计划时间内完成", sort_order: 9, default_visible: true },
  { code: "actual_completion_date", label: "实际完成时间", sort_order: 10, default_visible: true },
  { code: "owner_name", label: "责任人", sort_order: 11, default_visible: true },
  { code: "collaborator_names", label: "协作人", sort_order: 12, default_visible: true },
  { code: "document_links", label: "相关文档链接或佐证材料", sort_order: 13, default_visible: true },
]

export const deliveryColumnLabels: Record<FunctionalTaskColumn, string> =
  functionalTaskFieldDefinitions.reduce(
    (labels, definition) => {
      labels[definition.code] = definition.label
      return labels
    },
    {} as Record<FunctionalTaskColumn, string>,
  )

export function emptyFunctionalTask(ownerName = ""): FunctionalTaskDraft {
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
