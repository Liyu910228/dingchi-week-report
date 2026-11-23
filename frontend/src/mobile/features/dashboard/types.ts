export interface DashboardKpis {
  planned_tasks: number
  completion_rate: number
  completed_tasks: number
  risk_items: number
}

export interface DashboardTrendPoint {
  date: string
  label: string
  progress: number
  completion: number
}

export interface DashboardDistribution {
  name: string
  value: number
  color: string
}

export interface DashboardReport {
  updated_at?: string
  id: string
  role_code: string
  employee_id: string
  employee_name: string
  group_name: string | null
  period_start: string
  period_end: string
  status: string
  summary: string
  risk_level: string
  risk_blocked: boolean
  completion_rate?: number
}

export interface DashboardItem {
  /** 逻辑工作任务聚合元数据；输出成果明细不带这些字段。 */
  detail_count?: number
  completed_detail_count?: number
  detail_completion_rate?: number
  planned_detail_count?: number
  output_detail_count?: number
  detail_ids?: string[]
  id: string
  report_id: string
  customer_name_snapshot: string
  section_code?: string
  task_name_snapshot: string
  work_content?: string
  output_description?: string
  progress_percent: number | null
  quality_percent: number | null
  completion_rate: number | null
  on_time_status: string
  planned_completion_date: string | null
  progress_text: string
  delay_reason?: string
  next_action?: string
  owner_name_snapshot?: string
  collaborator_names?: string
  document_links?: string
}

export interface DashboardTeamTask extends DashboardItem {
  employee_id: string
  employee_name: string
  role_code: string
  role_name?: string
  group_name: string
  report_status: string
  report_period_start: string | null
  report_period_end: string | null
}

export interface DashboardMemberTaskPreview {
  detail_count?: number
  completed_detail_count?: number
  detail_completion_rate?: number
  id: string
  task_name: string
  customer_name: string
  progress_percent: number
  completion_rate: number
  status: string
  planned_completion_date: string
}

export interface DashboardMemberStats {
  progress_percent?: number
  group_id?: string | null
  employee_id: string
  employee_name: string
  role_code: string
  role_name: string
  group_name: string
  report_count: number
  task_count: number
  completed_task_count: number
  in_progress_task_count: number
  risk_task_count: number
  output_task_count: number
  completion_rate: number
  tasks: DashboardMemberTaskPreview[]
}

export interface DashboardGroupStats {
  progress_percent?: number
  group_id: string | null
  group_name: string
  member_count: number
  task_count: number
  completed_task_count: number
  in_progress_task_count: number
  risk_task_count: number
  output_task_count: number
  completion_rate: number
}

export interface DashboardSummary {
  scope: string
  period: { start: string; end: string }
  kpis: DashboardKpis
  trend: DashboardTrendPoint[]
  status_distribution: DashboardDistribution[]
  my_tasks: DashboardItem[]
  my_work_tasks?: DashboardItem[]
  team_work_tasks?: DashboardTeamTask[]
  team_output_items?: DashboardTeamTask[]
  output_count?: number
  output_distribution?: { section_code: string; value: number }[]
  my_plans: DashboardItem[]
  member_reports?: DashboardReport[]
  reports: DashboardReport[]
  team_tasks: DashboardTeamTask[]
  member_stats: DashboardMemberStats[]
  group_stats: DashboardGroupStats[]
}

export interface DashboardNextWeek {
  my_work_plans?: DashboardItem[]
  team_work_tasks?: DashboardTeamTask[]
  period: { start: string; end: string }
  my_plans: DashboardItem[]
  team_tasks: DashboardTeamTask[]
}
