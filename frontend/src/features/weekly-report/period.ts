import type { DailyWorkTask } from "./types"

// 周期调整时保留日报对应的星期和正文，所有模板复用。
export function moveDailyTasks(tasks: DailyWorkTask[], previous: string, next: string) {
  const offset = Date.parse(`${next}T00:00:00Z`) - Date.parse(`${previous}T00:00:00Z`)
  return tasks.map(task => ({
    ...task,
    work_date: new Date(Date.parse(`${task.work_date}T00:00:00Z`) + offset).toISOString().slice(0, 10),
  }))
}
