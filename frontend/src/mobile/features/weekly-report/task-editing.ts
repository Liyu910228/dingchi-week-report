import type { TaskDraft, TaskColumn } from "./task-draft"

export interface TaskTemplateOption { task: string; work: string; dimension?: string; customer?: string }
export type EditableTask = Omit<TaskDraft, "customer_name"> & {
  customer_name?: string
  dimension?: string
  quality_percent?: number | null
  completion_rate?: number | null
}
export type EditableTaskColumn = TaskColumn | "dimension" | "quality_percent" | "completion_rate"
export interface EditableTaskField { code: EditableTaskColumn; label: string }
