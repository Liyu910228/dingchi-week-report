import { computed, onMounted } from "vue"
import { RouterLink } from "vue-router"

import { useAuthStore } from "@/features/auth/store"
import { useDashboardStore } from "@/mobile/features/dashboard/store"


export function useLegacyDashboard() {
  const authStore = useAuthStore()
  const dashboardStore = useDashboardStore()
  const summary = computed(() => dashboardStore.summary)
  const workTasks = computed(() => summary.value.my_work_tasks ?? summary.value.my_tasks)
  const scopeLabel = computed(() => {
    const scope = summary.value.scope
    return scope === "all" ? "全员视角" : scope === "team" ? "团队视角" : "个人视角"
  })
  const customerDistribution = computed(() => {
    const grouped = new Map<string, number>()
    workTasks.value.forEach((task) => {
      const customer = task.customer_name_snapshot?.trim() || "内部事项"
      grouped.set(customer, (grouped.get(customer) || 0) + 1)
    })

    const colors = ["#2f80ed", "#12bfa0", "#7c5ce6", "#f4aa2f", "#53a7f8"]
    return Array.from(grouped.entries()).map(([name, value], index) => ({
      name,
      value,
      color: colors[index % colors.length],
    }))
  })
  const customerChartData = computed(() => (
    customerDistribution.value.length
      ? customerDistribution.value
      : [{ name: "暂无任务", value: 1, color: "#dfeafa" }]
  ))
  const nextPlans = computed(() => workTasks.value.slice(0, 2))
  const weekDays = ["周一", "周二", "周三", "周四", "周五"]

  onMounted(() => {
    void dashboardStore.load()
  })

  function formatPeriod(date: string) {
    return date.replaceAll("-", ".")
  }

  function riskLabel(value: string) {
    return value === "none" ? "无风险" : value === "high" ? "高风险" : value === "medium" ? "中风险" : "低风险"
  }
  return { authStore, dashboardStore, summary, workTasks, scopeLabel, customerDistribution, customerChartData, nextPlans, weekDays, formatPeriod, riskLabel }
}
