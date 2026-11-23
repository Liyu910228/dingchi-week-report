import { humanResourcesMonthlyTaskTemplates, humanResourcesTaskTemplates } from "./task-templates"
/** Excel 未设单独月度目标，经确认按五个模块汇总月度工作事项。 */
const monthlyGoal = "1、人力资源年度规划：人工成本预算、下半年工作计划\n2、外派员工年度规划：风险管理、成本管理\n3、外派员工日常管理：释放人员管理、诉讼案件\n4、人力资源管理：培训资料沉淀、人员配置、试用期人员管理、绩效核算、薪酬核发、内部培训管理"
export const humanResourcesMonthlyPlanSample = monthlyGoal
export const humanResourcesMonthlyPlanSampleFields = [{ label: "月度目标", value: monthlyGoal }] as const
export const humanResourcesMonthlyTaskSampleFields = humanResourcesMonthlyTaskTemplates.map((task, index) => ({ label: `计划 ${index + 1}`, rows: [
  { label: "模块", value: task.dimension }, { label: "工作任务", value: task.task }, { label: "工作内容", value: task.work },
] }))
export const humanResourcesWeeklyTaskSampleFields = humanResourcesTaskTemplates.map((task, index) => ({ label: `任务 ${index + 1}`, rows: [
  { label: "模块", value: task.dimension }, { label: "工作任务", value: task.task },
  { label: "工作内容", value: task.work },
] }))
export const humanResourcesWeeklyTaskSample = humanResourcesWeeklyTaskSampleFields.map(field => field.rows.map(row => `${row.label}：${row.value}`).join("\n")).join("\n\n")
