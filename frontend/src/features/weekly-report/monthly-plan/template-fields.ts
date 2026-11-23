export function monthlyPlanScopeLabel(templateCode: string): string {
  if (templateCode === "human_resources_v1") return "模块"
  if (templateCode === "functional_group_v1") return ""
  return ["recruitment_v1", "ito_sales_v1"].includes(templateCode) ? "维度" : "客户"
}

export function usesConfiguredCustomers(templateCode: string): boolean {
  return ["delivery_specialist_v1", "delivery_assistant_v1"].includes(templateCode)
}
