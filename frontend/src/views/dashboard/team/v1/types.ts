export interface TeamMemberSummary {
  employeeId: string
  employeeName: string
  roleName: string
  groupName: string
  completionRate: number
  taskCount: number
  completedTaskCount: number
  outputCount: number
  riskCount: number
}

export interface TeamReportEntry {
  updatedAt: string
  id: string
  employeeId: string
  employeeName: string
  roleName: string
  groupName: string
  summary: string
  completionRate: number
  status: string
  riskLevel: string
  periodStart: string
  periodEnd: string
}

export interface TeamPlanEntry {
  id: string
  title: string
  owner: string
  detail: string
  status: string
  plannedDate: string
  completionRate: number
}

export interface TeamOutcomeEntry {
  id: string
  owner: string
  taskName: string
  output: string
  risk: string
  completionRate: number
}
