import type { ApprovalRecord, ManagedMonthlyPlan } from "./types"

export type FlowState = "done" | "current" | "waiting" | "rejected"
export interface ApprovalFlowNode {
  id: string; title: string; person: string; result: string
  time: string | null; reason?: string; state: FlowState; terminal?: boolean
}

export function buildApprovalFlow(plan: ManagedMonthlyPlan | null, record: ApprovalRecord | null, managers: { id: string; name: string }[], applicant: string): ApprovalFlowNode[] {
  const active = record && plan?.status !== "draft" ? record : null
  const person = plan?.employee_name || applicant || "—"
  const nodes: ApprovalFlowNode[] = [
    { id: "start", title: "开始", person: "", result: "", time: null, state: "done", terminal: true },
    { id: "submit", title: "提交", person, result: active ? "已提交" : "待提交", time: active?.created_at || null, state: active ? "done" : "current" },
  ]
  const steps = active?.steps || managers.map((manager, index) => ({
    approver_id: manager.id, approver_name: manager.name, sort_order: index,
    status: "waiting", reason: "", acted_at: null,
  }))
  for (const step of steps) {
    const state: FlowState = step.status === "approved" ? "done" : step.status === "rejected" ? "rejected" : step.status === "pending" ? "current" : "waiting"
    const result = ({approved:"通过",rejected:"驳回",pending:"待审批",waiting:"未处理",cancelled:"已取消"} as Record<string,string>)[step.status] || "未处理"
    nodes.push({ id: `approval-${step.sort_order}`, title: "审批", person: step.approver_name, result, time: step.acted_at, reason: step.reason, state })
  }
  if (!steps.length) nodes.push({id:"approval",title:"审批",person:"无需审批",result:active?.status === "approved" ? "自动通过" : "提交后自动通过",time:active?.completed_at || null,state:active?.status === "approved" ? "done" : "waiting"})
  const finished = active?.status === "approved" || active?.status === "rejected"
  nodes.push({
    id:"end", title:"结束", person:"", result:"", time:null, terminal:true,
    state:finished ? active?.status === "rejected" ? "rejected" : "done" : "waiting",
  })
  return nodes
}
