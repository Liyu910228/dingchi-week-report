import { defineStore } from "pinia"
import { ref } from "vue"

import { getDashboardNextWeek, getDashboardSummary } from "./api"
import type { DashboardNextWeek, DashboardSummary } from "./types"

function emptySummary(): DashboardSummary {
  return {
    scope: "self",
    period: { start: "", end: "" },
    kpis: { planned_tasks: 0, completion_rate: 0, completed_tasks: 0, risk_items: 0 },
    trend: [],
    status_distribution: [],
    my_tasks: [],
    my_plans: [],
    reports: [],
    team_tasks: [],
    member_stats: [],
    group_stats: [],
  }
}

function emptyNextWeek(): DashboardNextWeek {
  return { period: { start: "", end: "" }, my_plans: [], team_tasks: [] }
}

export const useDashboardStore = defineStore("dashboard", () => {
  const summary = ref<DashboardSummary>(emptySummary())
  const nextWeek = ref<DashboardNextWeek>(emptyNextWeek())
  const isLoading = ref(false)
  const isLoaded = ref(false)
  const errorMessage = ref("")
  const selectedPeriodStart = ref("")

  async function load(periodStart?: string) {
    if (periodStart !== undefined) {
      selectedPeriodStart.value = periodStart
    }
    isLoading.value = true
    errorMessage.value = ""
    const period = selectedPeriodStart.value || undefined
    const [summaryResult, nextWeekResult] = await Promise.allSettled([
      getDashboardSummary(period),
      getDashboardNextWeek(period),
    ])
    if (summaryResult.status === "fulfilled") {
      summary.value = summaryResult.value
    } else {
      summary.value = emptySummary()
      const error = summaryResult.reason
      errorMessage.value = error instanceof Error ? error.message : "首页数据加载失败。"
    }
    nextWeek.value = nextWeekResult.status === "fulfilled" ? nextWeekResult.value : emptyNextWeek()
    isLoaded.value = true
    isLoading.value = false
  }

  return { summary, nextWeek, isLoading, isLoaded, errorMessage, selectedPeriodStart, load }
})
