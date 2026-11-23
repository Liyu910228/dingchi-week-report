import type { ReportPayload, WeeklyReportDetail, ReportTemplate } from "@/mobile/features/weekly-report/types"
import type { MonthlyPlanTask } from "@/mobile/features/weekly-report/monthly-plan/types"
import type { ManagedMonthlyPlan, ApprovalRecord, PlanGate, PlanChange,ApprovedPlanVersion,TaskProgressHistoryEntry } from "@/mobile/features/monthly-plan/types"
export type SubmissionKind = "monthly" | "weekly"
export interface AssignedCustomer {id:string;name:string}
export interface MonthlyPayload {summary:string;tasks:MonthlyPlanTask[];revision?:number}
export interface SubmissionPart {source_report_id?:string|null;source_updated_at?:string|null;source_plan_id?:string|null;source_revision?:number|null;source_submission_id?:string|null;id?:string;role_code:string;role_name:string;template_code:string;customers:AssignedCustomer[];template?:ReportTemplate;payload:Partial<ReportPayload> & MonthlyPayload;detail?:WeeklyReportDetail;monthly_plan?:PlanGate;monthly_approved?:boolean;monthly_message?:string}
export interface SubmissionDetail {plan:ManagedMonthlyPlan & {kind:SubmissionKind;period_start?:string;period_end?:string;legacy:boolean;role_codes:string[]};parts:SubmissionPart[];approvals:ApprovalRecord[];history?:ApprovedPlanVersion[];progress_history?:TaskProgressHistoryEntry[];managers?:{id:string;name:string}[];can_edit:boolean}
export interface SubmissionInput {change_reason?:string;base_revision?:number;month_key:string;period_start?:string;revision?:number;parts:SubmissionPart[]}
export interface SubmissionContext {positions:SubmissionPart[];managers:{id:string;name:string}[];kind:SubmissionKind}

export interface SubmissionChange {managers?:{id:string;name:string}[];plan:SubmissionDetail["plan"];change:PlanChange;base_snapshot:SubmissionSnapshot;snapshot:SubmissionSnapshot;approvals:ApprovalRecord[];can_edit:boolean}
export interface SubmissionSnapshot {change_reason?:string;month_key:string;summary:string;parts:SubmissionPart[]}
