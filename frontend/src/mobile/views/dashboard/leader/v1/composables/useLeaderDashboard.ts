import { computed, markRaw, onMounted, watch } from "vue"
import { BarChart3, ClipboardCheck, FileOutput, ListChecks, Network, Target } from "lucide-vue-next"

import { useAuthStore } from "@/features/auth/store"
import { useDashboardStore } from "@/mobile/features/dashboard/store"
import type { DashboardDistribution, DashboardTeamTask } from "@/mobile/features/dashboard/types"

import type { LeaderDepartment, LeaderPlan, LeaderRelation, LeaderResult } from "../types"

export function useLeaderDashboard() {
  const authStore = useAuthStore()
  const dashboardStore = useDashboardStore()
  const summary = computed(() => dashboardStore.summary)
  const tasks = computed<DashboardTeamTask[]>(() => summary.value.team_tasks || [])
  const nextWeekTasks = computed<DashboardTeamTask[]>(() => dashboardStore.nextWeek.team_work_tasks ?? dashboardStore.nextWeek.team_tasks ?? [])
  const currentTasks = computed<DashboardTeamTask[]>(() => {
    const selectedStart = summary.value.period.start?.slice(0, 10)
    if (!selectedStart) return tasks.value
    return tasks.value.filter((task) => task.report_period_start?.slice(0, 10) === selectedStart)
  })
  const workTasks = computed<DashboardTeamTask[]>(() => summary.value.team_work_tasks ?? currentTasks.value)
  const outputTotal = computed(() => summary.value.output_count ?? currentTasks.value.filter(task => task.output_description?.trim()).length)
  const memberStats = computed(() => summary.value.member_stats || [])
  const groupStats = computed(() => summary.value.group_stats || [])

  const roleNameMap: Record<string, string> = {
    system_admin: "系统管理员",
    president: "总裁",
    delivery_manager: "交付经理",
    delivery_specialist: "交付专员",
    delivery_assistant: "交付助理",
    recruitment_manager: "招聘经理",
    recruitment_specialist: "招聘专员",
    ito_sales: "ITO销售",
    innovation_sales: "创新业务销售",
    innovation_business_sales: "创新业务销售",
    functional_group: "职能组",
  }

  function formatDate(value: string | null | undefined) {
    return value ? value.slice(0, 10).replaceAll("-", ".") : "—"
  }

  function sectionLabel(value: string | null | undefined) {
    const labels: Record<string, string> = { overall: "总体事项", recruitment: "招聘工作", delivery: "交付工作", sales: "销售工作", risk: "风险事项", weekly_tasks: "周报任务", other: "其他事项" }
    return labels[value || ""] || value || "其他事项"
  }

  function splitCollaborators(value: string | null | undefined) {
    return (value || "").split(/[、,，;/；]/).map((item) => item.trim()).filter(Boolean)
  }

  const departments = computed<LeaderDepartment[]>(() => {
    return groupStats.value.map((group) => ({
      name: group.group_name,
      rate: Math.round(group.completion_rate),
      taskCount: group.task_count,
    }))
      .sort((left, right) => right.rate - left.rate || right.taskCount - left.taskCount)
      .slice(0, 4)
  })

  const outputDistribution = computed<DashboardDistribution[]>(() => {
    const colors = ["#168cff", "#00bcd7", "#ffca38", "#944aff", "#12b98d"]
    if (summary.value.output_distribution) return summary.value.output_distribution.map((item, index) => ({
      name: sectionLabel(item.section_code), value: item.value, color: colors[index % colors.length],
    })).sort((a, b) => b.value - a.value).slice(0, 5)
    const grouped = new Map<string, number>()
    for (const task of currentTasks.value.filter((item) => Boolean(item.output_description?.trim()))) {
      const key = sectionLabel(task.section_code)
      grouped.set(key, (grouped.get(key) || 0) + 1)
    }
    return Array.from(grouped, ([name, value], index) => ({ name, value, color: colors[index % colors.length] }))
      .sort((left, right) => right.value - left.value)
      .slice(0, 5)
  })

  const results = computed<LeaderResult[]>(() => (summary.value.team_output_items ?? currentTasks.value).filter((task) => Boolean(task.output_description?.trim())).slice(0, 4).map((task) => ({
    id: task.id,
    name: task.output_description || "",
    owner: task.employee_name,
    category: sectionLabel(task.section_code),
    file: task.document_links || "—",
  })))

  const plans = computed<LeaderPlan[]>(() => [...nextWeekTasks.value].sort((left, right) => String(left.planned_completion_date || "").localeCompare(String(right.planned_completion_date || ""))).slice(0, 4).map((task) => ({
    id: task.id,
    name: task.task_name_snapshot || "未命名任务",
    note: task.progress_text || task.work_content || "暂无说明",
    date: formatDate(task.planned_completion_date),
    owner: task.employee_name,
  })))

  const relations = computed<LeaderRelation[]>(() => {
    const grouped = new Map<string, number>()
    for (const task of workTasks.value) {
      for (const name of splitCollaborators(task.collaborator_names)) grouped.set(name, (grouped.get(name) || 0) + 1)
    }
    return Array.from(grouped, ([name, count]) => ({ id: name, name, count })).sort((left, right) => right.count - left.count).slice(0, 6)
  })

  const planCoverage = computed(() => {
    if (!workTasks.value.length) return 0
    return Math.round((workTasks.value.filter((task) => Boolean(task.planned_completion_date)).length / workTasks.value.length) * 100)
  })

  const metricCards = computed(() => [
    { label: "本周任务", value: summary.value.kpis.planned_tasks, hint: "当前周期任务总数", tone: "blue" as const, icon: markRaw(ListChecks) },
    { label: "成果输出", value: outputTotal.value, hint: "本周已沉淀成果", tone: "purple" as const, icon: markRaw(FileOutput) },
    { label: "整体完成率", value: `${Math.round(summary.value.kpis.completion_rate)}%`, hint: "进展与质量综合", tone: "green" as const, icon: markRaw(Target) },
    { label: "计划覆盖率", value: `${planCoverage.value}%`, hint: "已设置计划完成时间", tone: "amber" as const, icon: markRaw(ClipboardCheck) },
    { label: "协同人数", value: relations.value.length, hint: "参与跨团队协作", tone: "red" as const, icon: markRaw(Network) },
  ])

  onMounted(() => { void dashboardStore.load() })
  watch(() => authStore.effectiveRole?.role_code, () => { void dashboardStore.load() })

  function handlePeriodChange(periodStart: string) {
    void dashboardStore.load(periodStart)
  }

  return { authStore, dashboardStore, summary, tasks, nextWeekTasks, currentTasks, workTasks, outputTotal, memberStats, groupStats, roleNameMap, departments, outputDistribution, results, plans, relations, planCoverage, metricCards, formatDate, sectionLabel, splitCollaborators, handlePeriodChange }
}
