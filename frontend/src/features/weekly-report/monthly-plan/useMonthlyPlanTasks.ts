import { ref } from "vue"

import { monthlyPlanScopeLabel } from "./template-fields"
import { getMonthlyPlanGate } from "@/features/monthly-plan/api"
import type { MonthlyPlanTask, MonthlyPlanTaskPayload } from "./types"

export function useMonthlyPlanTasks() {
  const approved = ref(false)
  const summary = ref("")
  const gateMessage = ref("")
  const tasks = ref<MonthlyPlanTask[]>([])
  const isLoading = ref(false)
  const errorMessage = ref("")
  let loadedMonth = ""
  let requestVersion = 0

  function setTasks(monthKey: string, items: MonthlyPlanTask[]) {
    requestVersion += 1
    tasks.value = items.map((item) => ({ ...item }))
    loadedMonth = monthKey
    isLoading.value = false
    errorMessage.value = ""
  }

  async function load(monthKey: string) {
    const version = ++requestVersion
    loadedMonth = ""
    tasks.value = []
    isLoading.value = true
    approved.value = false
    errorMessage.value = ""
    try {
      const response = await getMonthlyPlanGate(monthKey)
      if (version !== requestVersion) return
      tasks.value = response.tasks
      approved.value = response.approved
      summary.value = response.plan?.summary || ""
      gateMessage.value = response.message
      loadedMonth = monthKey
    } catch (error) {
      if (version === requestVersion) {
        errorMessage.value = error instanceof Error ? error.message : "月度计划加载失败，请重试。"
      }
    } finally {
      if (version === requestVersion) isLoading.value = false
    }
  }

  function buildPayload(monthKey: string): MonthlyPlanTaskPayload[] {
    if (isLoading.value || loadedMonth !== monthKey || errorMessage.value) {
      throw new Error("请等待月度计划加载完成，加载失败时请先重试。")
    }
    return tasks.value.map(({ id: _id, updated_at: _updated, sort_order: _sort, ...task }) => ({
      ...task,
      scope_name: (task.scope_name || "").trim(),
      work_task: task.work_task.trim(),
      work_content: task.work_content?.trim(),
      output_description: task.output_description || "",
      planned_date: task.planned_date || null,
    }))
  }

  function validateBeforeSave(summary: string, templateCode: string) {
    if (!summary.trim()) throw new Error("请先填写并保存当前月份的月度目标，再保存周报。")
    if (!tasks.value.length) throw new Error("请至少填写一条月度计划，再保存周报。")
    const label = monthlyPlanScopeLabel(templateCode)
    if (label && tasks.value.some((task) => !task.scope_name?.trim())) {
      throw new Error(`月度计划中的${label}不能为空。`)
    }
    if (tasks.value.some((task) => !task.work_task.trim())) {
      throw new Error("月度计划中的工作任务不能为空。")
    }
  }

  return { approved, summary, gateMessage, tasks, isLoading, errorMessage, load, setTasks, buildPayload, validateBeforeSave }
}
