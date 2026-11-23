import type {TaskAttachment} from "../task-draft"
import type { TaskTextMetadata } from "../task-texts"

/** 月度任务扩展字段；旧快照缺省时使用空文本、0%和进行中。 */
export interface MonthlyTaskProgress {
  progress_text?: string
  progress_percent?: number | null
  quality_percent?: number | null
  completion_rate?: number | null
  delay_reason?: string
  on_time_status?: string
  actual_completion_date?: string
  owner_id?: string | null
  owner_name?: string
  collaborator_names?: string
  attachments?: TaskAttachment[]
  document_links?: string
  progress_revision?: number
  progress_updated_at?: string | null
  progress_updated_by?: string | null
  progress_updated_by_name?: string
}

/** 按员工、角色、月份共用的月度计划明细。ID 为字符串，排序按数组顺序。 */
export interface MonthlyPlanTask extends MonthlyTaskProgress, Pick<TaskTextMetadata, "customer_id" | "task_source" | "task_template" | "task_values" | "dimension_source" | "dimension_template" | "dimension_values" | "customer_source" | "customer_template" | "customer_values"> {
  id: string
  /** 当前月度计划内的客户/维度、工作任务分组；省略时每行独立。 */
  scope_group_key?: string
  task_group_key?: string
  content_group_key?: string
  scope_name?: string
  work_task: string
  /** 主要工作内容；旧审批快照省略时按空文本显示。 */
  work_content?: string
  output_description?: string
  planned_date?: string | null
  sort_order?: number
  updated_at?: string
}

export interface MonthlyPlanTaskPayload extends MonthlyTaskProgress, Pick<TaskTextMetadata, "customer_id" | "task_source" | "task_template" | "task_values" | "dimension_source" | "dimension_template" | "dimension_values" | "customer_source" | "customer_template" | "customer_values"> {
  /** 当前月度计划内的客户/维度、工作任务分组；省略时每行独立。 */
  scope_group_key?: string
  task_group_key?: string
  content_group_key?: string
  scope_name?: string
  work_task: string
  work_content?: string
  output_description?: string
  planned_date?: string | null
}
