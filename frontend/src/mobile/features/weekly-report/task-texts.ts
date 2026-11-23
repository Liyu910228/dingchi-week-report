import type { ReportItem } from "./types"
export interface TaskTextMetadata {
  customer_id?: string | null
  customer_text_id?: string | null
  customer_group_key?: string
  customer_source?: "custom" | "template"
  customer_template?: string
  customer_values?: string[]
  dimension_text_id?: string | null
  dimension_group_key?: string
  dimension_source?: "custom" | "template"
  dimension_template?: string
  dimension_values?: string[]
  task_text_id?: string | null
  work_content_text_id?: string | null
  task_group_key?: string
  work_content_group_key?: string
  task_source?: "custom" | "template"
  task_template?: string
  task_values?: string[]
}
export function taskTextMetadata(item: TaskTextMetadata): TaskTextMetadata {
  return { customer_id: item.customer_id, customer_text_id: item.customer_text_id, customer_group_key: item.customer_group_key || item.customer_text_id || undefined,
    customer_source: item.customer_source || "custom", customer_template: item.customer_template || "", customer_values: [...(item.customer_values || [])],
    dimension_text_id: item.dimension_text_id, dimension_group_key: item.dimension_group_key || item.dimension_text_id || undefined,
    dimension_source: item.dimension_source || "custom", dimension_template: item.dimension_template || "", dimension_values: [...(item.dimension_values || [])],
    task_text_id: item.task_text_id, work_content_text_id: item.work_content_text_id,
    task_group_key: item.task_group_key || item.task_text_id || undefined,
    work_content_group_key: item.work_content_group_key || item.work_content_text_id || undefined,
    task_source: item.task_source || "custom", task_template: item.task_template || "", task_values: [...(item.task_values || [])] }
}
export function loadedTaskTextMetadata(item: ReportItem): TaskTextMetadata { return taskTextMetadata(item) }
export function renderTaskTemplate(template: string, values: string[]): string {
  return template.split(/[?？]/).map((part, index) => part + (values[index] || "")).join("")
}

/** 展示模板任务时保留未填写的问号，不改变实际保存的占位值。 */
export function previewTaskTemplate(template: string, values: string[]): string {
  let index = 0
  return template.replace(/[?？]/g, (placeholder) => {
    const value = values[index++]
    return value?.trim() ? value : placeholder
  })
}
