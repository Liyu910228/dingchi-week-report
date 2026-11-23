import { computed, markRaw, onMounted, watch } from "vue"
import { ClipboardCheck, Handshake, ListChecks, Target, UsersRound } from "lucide-vue-next"

import { isWorkTaskCompleted } from "@/features/dashboard/task-metrics"
import { useAuthStore } from "@/features/auth/store"
import { useDashboardStore } from "@/features/dashboard/store"
import type { DashboardDistribution, DashboardMemberStats, DashboardTeamTask } from "@/features/dashboard/types"

import type { TeamMemberSummary, TeamPlanEntry, TeamReportEntry } from "../types"

export function useTeamDashboard() {
  const authStore = useAuthStore()
  const dashboardStore = useDashboardStore()
  const summary = computed(() => dashboardStore.summary)

  const roleNameMap: Record<string, string> = {
    system_admin: "系统管理员",
    president: "总裁",
    delivery_manager: "交付经理",
    delivery_specialist: "交付专员",
    delivery_assistant: "交付助理",
    recruitment_manager: "招聘经理",
    recruitment_specialist: "招聘专员",
    ito_sales: "ITO销售",
    innovation_business_sales: "创新业务销售",
  }

  const reports = computed<TeamReportEntry[]>(() => summary.value.reports.map((report) => ({
    id: report.id,
    updatedAt: report.updated_at || "",
    employeeId: report.employee_id,
    employeeName: report.employee_name || "未命名成员",
    roleName: roleNameMap[report.role_code] || report.role_code || "团队成员",
    groupName: report.group_name || "未分组",
    summary: report.summary || "",
    completionRate: Number(report.completion_rate || 0),
    status: report.status || "进行中",
    riskLevel: report.risk_level || "none",
    periodStart: formatDate(report.period_start),
    periodEnd: formatDate(report.period_end),
  })))

  const submissionReports = computed<TeamReportEntry[]>(() => (summary.value.member_reports || summary.value.reports).map((report) => ({
    id: report.id,
    updatedAt: report.updated_at || "",
    employeeId: report.employee_id,
    employeeName: report.employee_name || "未命名成员",
    roleName: roleNameMap[report.role_code] || report.role_code || "团队成员",
    groupName: report.group_name || "未分组",
    summary: report.summary || "",
    completionRate: Number(report.completion_rate || 0),
    status: report.status || "进行中",
    riskLevel: report.risk_level || "none",
    periodStart: formatDate(report.period_start),
    periodEnd: formatDate(report.period_end),
  })))

  const teamTasks = computed<DashboardTeamTask[]>(() => summary.value.team_work_tasks ?? summary.value.team_tasks ?? [])
  const nextWeekTasks = computed<DashboardTeamTask[]>(() => dashboardStore.nextWeek.team_work_tasks ?? dashboardStore.nextWeek.team_tasks ?? [])
  const memberStats = computed<DashboardMemberStats[]>(() => summary.value.member_stats || [])

  const currentReports = computed(() => {
    const currentStart = parseDate(summary.value.period.start)
    if (!currentStart) return reports.value
    return reports.value.filter((report) => {
      const periodStart = parseDate(report.periodStart)
      return periodStart?.getTime() === currentStart.getTime()
    })
  })

  const currentTasks = computed(() => {
    const currentStart = parseDate(summary.value.period.start)
    if (!currentStart) return teamTasks.value
    return teamTasks.value.filter((task) => {
      const periodStart = parseDate(task.report_period_start)
      return periodStart?.getTime() === currentStart.getTime()
    })
  })

  const members = computed<TeamMemberSummary[]>(() => memberStats.value
    .map((member) => ({
      employeeId: member.employee_id || `name:${member.employee_name}`,
      employeeName: member.employee_name || "未命名成员",
      roleName: member.role_name || member.role_code || "团队成员",
      groupName: member.group_name || "未分组",
      completionRate: member.completion_rate,
      taskCount: member.task_count,
      completedTaskCount: member.completed_task_count,
      outputCount: member.output_task_count,
      riskCount: member.risk_task_count,
    })))

  const myReport = computed(() => {
    const userId = authStore.user?.id
    if (!userId) return null
    const report = currentReports.value.find((item) => item.employeeId === userId)
      || reports.value.find((item) => item.employeeId === userId)
    if (!report) return null
    const work = teamTasks.value.filter(task => task.report_id === report.id)
    const completionRate = work.length ? work.reduce((total, task) => total + taskCompletionRate(task), 0) / work.length : 0
    return { ...report, completionRate }
  })

  const plans = computed<TeamPlanEntry[]>(() => {
    return [...nextWeekTasks.value]
      .sort((left, right) => String(left.planned_completion_date || "").localeCompare(String(right.planned_completion_date || "")))
      .slice(0, 8)
      .map((task) => ({
        id: `plan-${task.id}`,
        title: String(task.next_action || "").trim() || task.task_name_snapshot || "未命名任务",
        owner: task.employee_name || "未命名成员",
        detail: `${task.employee_name || "未命名成员"} · ${task.group_name || task.section_code || "未分组"}`,
        status: taskStatusText(task),
        plannedDate: formatDate(task.planned_completion_date || ""),
        completionRate: taskCompletionRate(task),
      }))
  })

  const currentReportTotal = computed(() => submissionReports.value.filter(report => report.status === "completed" && members.value.some(member => member.employeeId === report.employeeId)).length)
  const currentTaskTotal = computed(() => memberStats.value.reduce((total, member) => total + member.task_count, 0))
  const currentCompletedTaskTotal = computed(() => memberStats.value.reduce((total, member) => total + member.completed_task_count, 0))
  const currentRiskTaskTotal = computed(() => memberStats.value.reduce((total, member) => total + member.risk_task_count, 0))
  const currentCollaborationTotal = computed(() => currentTasks.value.filter((task) => String(task.collaborator_names || "").trim()).length)
  const ownTaskCount = computed(() => {
    const userId = authStore.user?.id
    return userId ? currentTasks.value.filter((task) => task.employee_id === userId).length : 0
  })
  const ownPlanCount = computed(() => {
    const userId = authStore.user?.id
    return userId ? nextWeekTasks.value.filter((task) => task.employee_id === userId).length : 0
  })
  const currentCompletionRate = computed(() => {
    if (!currentTaskTotal.value) return 0
    const weightedTotal = memberStats.value.reduce(
      (total, member) => total + member.completion_rate * member.task_count,
      0,
    )
    return weightedTotal / currentTaskTotal.value
  })

  const currentStatusDistribution = computed<DashboardDistribution[]>(() => {
    if (!currentTaskTotal.value) return []
    const risks = currentRiskTaskTotal.value
    const completed = currentCompletedTaskTotal.value
    const inProgress = Math.max(0, currentTaskTotal.value - completed - risks)
    return [
      { name: "进行中", value: inProgress, color: "#2f80ed" },
      { name: "已完成", value: completed, color: "#12b886" },
      { name: "延期/风险", value: risks, color: "#f05d5e" },
    ].filter((item) => item.value > 0)
  })

  const metricCards = computed(() => [
    { label: "团队成员", value: members.value.length, tone: "blue" as const, icon: markRaw(UsersRound) },
    { label: "周报提交", value: `${currentReportTotal.value}/${members.value.length}`, tone: "blue" as const, icon: markRaw(ClipboardCheck) },
    { label: "团队完成率", value: `${Math.round(currentCompletionRate.value)}%`, tone: "purple" as const, icon: markRaw(Target) },
    { label: "本周任务", value: currentTaskTotal.value, tone: "green" as const, icon: markRaw(ListChecks) },
    { label: "协同事项", value: currentCollaborationTotal.value, tone: "orange" as const, icon: markRaw(Handshake) },
  ])

  onMounted(() => {
    void dashboardStore.load()
  })

  watch(() => authStore.effectiveRole?.role_code, () => {
    void dashboardStore.load()
  })

  function handlePeriodChange(periodStart: string) {
    void dashboardStore.load(periodStart)
  }

  function formatDate(value: string) {
    if (!value) return ""
    return value.slice(0, 10).replaceAll("-", ".")
  }

  function parseDate(value: string | null | undefined) {
    if (!value) return null
    const normalized = value.slice(0, 10).replaceAll(".", "-")
    const parsed = new Date(`${normalized}T00:00:00`)
    return Number.isNaN(parsed.getTime()) ? null : parsed
  }

  function taskCompletionRate(task: DashboardTeamTask) {
    const value = task.completion_rate ?? task.progress_percent ?? 0
    const number = Number(value)
    return Number.isFinite(number) ? Math.min(100, Math.max(0, number)) : 0
  }

  function isTaskCompleted(task: DashboardTeamTask) {
    return isWorkTaskCompleted(task)
  }

  function isTaskRisk(task: DashboardTeamTask) {
    const status = String(task.on_time_status || "").toLowerCase()
    return ["overdue", "late"].includes(status) || Boolean(String(task.delay_reason || "").trim())
  }

  function taskRiskText(task: DashboardTeamTask) {
    const status = String(task.on_time_status || "").toLowerCase()
    const reason = String(task.delay_reason || "").trim()
    if (status === "overdue") return reason ? `已逾期：${reason}` : "已逾期"
    if (status === "late") return reason ? `已延期：${reason}` : "已延期"
    if (reason) return `风险：${reason}`
    return ""
  }

  function taskStatusText(task: DashboardTeamTask) {
    if (isTaskRisk(task)) return taskRiskText(task)
    return isTaskCompleted(task) ? "已完成" : "进行中"
  }

  return { authStore, dashboardStore, summary, roleNameMap, reports, submissionReports, teamTasks, nextWeekTasks, memberStats, currentReports, currentTasks, members, myReport, plans, currentReportTotal, currentTaskTotal, currentCompletedTaskTotal, currentRiskTaskTotal, currentCollaborationTotal, ownTaskCount, ownPlanCount, currentCompletionRate, currentStatusDistribution, metricCards, handlePeriodChange, formatDate, parseDate, taskCompletionRate, isTaskCompleted, isTaskRisk, taskRiskText, taskStatusText }
}
