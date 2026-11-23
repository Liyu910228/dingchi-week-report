import { splitTaskBlocks } from "@/mobile/features/weekly-report/task-groups"
import { createId } from "@/utils/id"
import { renderTaskTemplate } from "@/mobile/features/weekly-report/task-texts"
import type { MonthlyPlanTask } from "@/mobile/features/weekly-report/monthly-plan/types"

export type MonthlyGroupLevel = "scope" | "task" | "content"
export function monthlyGroupKey(task: MonthlyPlanTask, level: MonthlyGroupLevel): string {
  const scope = task.scope_group_key || task.id
  const parent = `${scope}:${task.task_group_key || task.id}`
  return level === "scope" ? scope : level === "task" ? parent : `${parent}:${task.content_group_key || task.id}`
}
export function splitMonthlyBlocks(value: string): string[] {
  const blocks = splitTaskBlocks(value)
  return blocks.length ? blocks : [""]
}
/** 普通换行保留，任务块下分别展开工作内容块，不凭相同文字合并独立任务。 */
export function expandMonthlyTasks(tasks: MonthlyPlanTask[]): MonthlyPlanTask[] {
  const result: MonthlyPlanTask[] = []
  for (let start = 0; start < tasks.length;) {
    const first = tasks[start]!
    let end = start + 1
    while (end < tasks.length && monthlyGroupKey(tasks[end]!, "task") === monthlyGroupKey(first, "task")) end++
    const group = tasks.slice(start, end)
    const templates = splitMonthlyBlocks(first.task_source === "template" && first.task_template ? first.task_template : first.work_task)
    if (templates.length === 1 && group.every(task => splitMonthlyBlocks(task.work_content || "").length === 1)) result.push(...group)
    else {
      const contentKeys = new Map<string, string>()
      let offset = 0
      for (const [taskIndex, text] of templates.entries()) {
        const count = (text.match(/[?？]/g) || []).length
        const values = (first.task_values || []).slice(offset, offset + count)
        offset += count
        const template = first.task_source === "template" ? { task_template: text, task_values: values,
          work_task: renderTaskTemplate(text, values) } : { work_task: text }
        const taskKey = taskIndex === 0 ? first.task_group_key || first.id : createId()
        for (const task of group) for (const [contentIndex, work_content] of splitMonthlyBlocks(task.work_content || "").entries()) {
          const contentId = `${task.content_group_key || task.id}:${contentIndex}`
          const contentKey = contentKeys.get(contentId) || (contentIndex === 0 ? task.content_group_key || task.id : createId())
          contentKeys.set(contentId, contentKey)
          result.push({ ...task, ...template, work_content,
            id: taskIndex === 0 && contentIndex === 0 ? task.id : `draft-${createId()}`,
            scope_group_key: first.scope_group_key || first.id, task_group_key: taskKey,
            content_group_key: contentKey,
          })
        }
      }
    }
    start = end
  }
  return result
}
export function patchMonthlyTasks(tasks: MonthlyPlanTask[], id: string, fields: Partial<MonthlyPlanTask>): MonthlyPlanTask[] {
  const origin = tasks.find(task => task.id === id)
  if (!origin) return tasks
  const scopeFields = ["scope_name", "dimension_source", "dimension_template", "dimension_values", "customer_source", "customer_template", "customer_values"] as const
  const taskFields = ["work_task", "task_source", "task_template", "task_values"] as const
  return expandMonthlyTasks(tasks.map(task => {
    const patch: Partial<MonthlyPlanTask> = task.id === id ? { ...fields } : {}
    for (const [level, names] of [["scope", scopeFields], ["task", taskFields], ["content", ["work_content"]]] as const) {
      if (monthlyGroupKey(task, level) !== monthlyGroupKey(origin, level)) continue
      for (const name of names) if (name in fields) Object.assign(patch, { [name]: fields[name] })
    }
    return Object.keys(patch).length ? { ...task, ...patch } : task
  }))
}
export function insertMonthlyChild(tasks: MonthlyPlanTask[], id: string, level: MonthlyGroupLevel): MonthlyPlanTask[] {
  const index = tasks.findIndex(task => task.id === id)
  const origin = tasks[index]
  if (!origin) return tasks
  const scopeKey = origin.scope_group_key || origin.id
  const taskKey = origin.task_group_key || origin.id
  const contentKey = origin.content_group_key || origin.id
  const child: MonthlyPlanTask = { ...origin, id: `draft-${createId()}`, scope_group_key: scopeKey,
    output_description: "", planned_date: null,
    progress_text: "", progress_percent: 0, quality_percent: 0, completion_rate: 0,
    delay_reason: "", on_time_status: "in_progress", actual_completion_date: "", document_links: "", attachments: [],
    work_content: level === "content" ? origin.work_content : "",
    content_group_key: level === "content" ? contentKey : createId(),
    task_group_key: level === "scope" ? createId() : taskKey,
    ...(level === "scope" ? { work_task: "", task_source: "custom", task_template: "", task_values: [] } : {}),
  }
  const normalized = tasks.map(task => {
    if (monthlyGroupKey(task, "scope") !== monthlyGroupKey(origin, "scope")) return task
    return { ...task, scope_group_key: scopeKey,
      ...(monthlyGroupKey(task, "task") === monthlyGroupKey(origin, "task") ? { task_group_key: taskKey } : {}),
      ...(monthlyGroupKey(task, "content") === monthlyGroupKey(origin, "content") ? { content_group_key: contentKey } : {}),
    }
  })
  let after = index + 1
  while (after < tasks.length && monthlyGroupKey(tasks[after]!, level) === monthlyGroupKey(origin, level)) after++
  return [...normalized.slice(0, after), child, ...normalized.slice(after)]
}
export function monthlyRowSpan(tasks: MonthlyPlanTask[], index: number, level: MonthlyGroupLevel): number {
  const key = monthlyGroupKey(tasks[index]!, level)
  if (index && monthlyGroupKey(tasks[index - 1]!, level) === key) return 0
  let count = 1
  while (index + count < tasks.length && monthlyGroupKey(tasks[index + count]!, level) === key) count++
  return count
}
