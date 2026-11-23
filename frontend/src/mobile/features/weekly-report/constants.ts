export const REPORT_ROLE_NAMES: Record<string, string> = {
  recruitment_specialist: "招聘专员",
  delivery_specialist: "交付专员",
  delivery_assistant: "交付助理",
  recruitment_manager: "招聘经理",
  delivery_manager: "交付经理",
  president: "总裁",
  system_admin: "系统管理员",
  ito_sales: "ITO销售",
  innovation_sales: "创新业务销售",
  functional_group: "职能组",
}

export function getReportRoleName(roleCode: string, roleName?: string | null): string {
  return roleName || REPORT_ROLE_NAMES[roleCode] || roleCode
}
