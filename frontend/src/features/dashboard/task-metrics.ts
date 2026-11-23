import type { DashboardItem } from "./types"

export function isWorkTaskCompleted(task: DashboardItem): boolean {
  if (task.detail_count !== undefined) return task.completed_detail_count === task.detail_count
  return ["completed", "on_time", "late"].includes(task.on_time_status) || Number(task.progress_percent || 0) >= 100
}
export function taskCompletionText(task: DashboardItem): string {
  if (task.detail_count !== undefined) {
    return `${task.completed_detail_count || 0}/${task.detail_count}（${Math.round(task.detail_completion_rate || 0)}%）`
  }
  return task.completion_rate === null ? "—" : `${Math.round(task.completion_rate)}%`
}
