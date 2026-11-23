import type { MonthlyPlanTask } from "@/mobile/features/weekly-report/monthly-plan/types"

export interface RoleGoalSummary { role_code: string; role_name: string; summary: string }

export interface ManagedMonthlyPlan {
  role_summaries?: RoleGoalSummary[]
  id: string
  employee_id: string
  employee_name: string
  group_id: string | null
  group_name: string
  role_code: string
  role_name?: string
  template_code: string
  month_key: string
  summary: string
  status: string
  revision: number
  rejection_reason: string
  updated_at: string
  created_at?: string
  can_approve: boolean
  children?: PlanChange[]
  can_create_change?: boolean
}
export interface PlanSnapshot { role_code?: string; role_name?: string; change_reason?: string; parts?: import("@/mobile/features/submissions/types").SubmissionPart[]; summary: string; tasks: MonthlyPlanTask[]; template_code: string; month_key: string }
export interface ApprovalRecord {
  id: string
  revision: number
  status: string
  created_at: string
  completed_at?: string | null
  can_approve: boolean
  snapshot: PlanSnapshot
  steps: { approver_id: string; approver_name: string; approver_role_code?:string; sort_order: number; status: string; reason: string; acted_at: string | null }[]
  plan_id?: string
  month_key?: string
  role_code?: string
  role_name?: string
  employee_name?: string
  group_name?: string
  my_status?: string
  my_reason?: string
  my_acted_at?: string | null
  process_type?: "initial" | "change"
  change_id?: string | null
  base_snapshot?: PlanSnapshot | null
}
export interface PlanHistory {
  id: string; revision: number; action: string; changed_by: string; created_at: string
  snapshot: PlanSnapshot
  changes: { summary: { before: string; after: string }; added: MonthlyPlanTask[]; deleted: MonthlyPlanTask[]; modified: {before: MonthlyPlanTask; after: MonthlyPlanTask}[] }
}
export interface ApprovedPlanVersion extends ApprovalRecord { version: number; process_type: "initial" | "change" }
export interface PlanChange { role_summaries?: RoleGoalSummary[]; id:string; plan_id:string; status:string; revision:number; base_revision:number; summary:string; rejection_reason:string; created_at:string; updated_at:string }
export interface ChangeDetail { plan:ManagedMonthlyPlan; change:PlanChange; base_snapshot:PlanSnapshot; snapshot:PlanSnapshot; approvals:ApprovalRecord[]; can_edit:boolean }
export interface PlanDetail { plan: ManagedMonthlyPlan; tasks: MonthlyPlanTask[]; approvals: ApprovalRecord[]; history: ApprovedPlanVersion[]; progress_history?: TaskProgressHistoryEntry[]; can_edit: boolean; can_create_change?:boolean }
export interface TaskProgressHistoryEntry { id:string;task_id:string;task_name:string;revision:number;changed_by:string;changed_by_name:string;created_at:string;before:Record<string,unknown>;after:Record<string,unknown>;changes:{field:string;label:string;before:unknown;after:unknown}[] }
export interface PlanContext { template_code: string; can_create: boolean; warning: string; managers: {id: string; name: string}[]; pending_approval_count?:number; has_approval_tasks?: boolean }
export interface PlanInput { month_key: string; summary: string; tasks: MonthlyPlanTask[]; revision?: number }
export type PlanListView = "mine" | "members" | "approvals" | "shared"
export interface PlanFilters { employee_name?: string; role_code?: string; view?: PlanListView; month_key?: string; status?: string; employee_id?: string; group_id?: string; pending_only?: boolean; page?: number; page_size?: number }
export interface PlanList { items: ManagedMonthlyPlan[]; approvals: ApprovalRecord[]; page: number; page_size: number; total: number; total_pages: number; pending_approval_count?:number; has_approval_tasks?: boolean }
export interface PlanGate { approved: boolean; message: string; plan: ManagedMonthlyPlan | null; tasks: MonthlyPlanTask[] }

export const planStatusLabels: Record<string, string> = { draft: "草稿", pending: "待审批", approved: "已通过", rejected: "已驳回", waiting: "未轮到", cancelled: "已取消", deleted: "已删除" }
