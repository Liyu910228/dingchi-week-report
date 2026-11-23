import { itoSalesMonthlyTaskTemplates, itoSalesTaskTemplates as taskExamples } from "./task-templates"

/** ITO 销售 Excel 中“月度目标”行的完整填写样例。 */
const monthlyGoal = `1、本月签约目标：万元
2、目标客户签约数
1）新增商机数：
2）新合同签订数：
3）老合同续签数：
3、本月回款目标：万元
4、新客户开发：`

export const itoSalesMonthlyPlanSample = monthlyGoal
export const itoSalesMonthlyPlanSampleFields = [
  { label: "月度目标", value: monthlyGoal },
] as const



/** 月度与周度指引分别维护，区域业务中的地区、月份及业务数据统一使用问号占位。 */
export const itoSalesMonthlyTaskSampleFields = itoSalesMonthlyTaskTemplates.map((task, index) => ({
  label: `任务 ${index + 1}`,
  rows: [
    { label: "维度", value: task.customer },
    { label: "工作任务", value: task.task || "（暂无填写）" },
    { label: "主要工作指引", value: task.work || "（暂无填写）" },
    ...(task.work === "拜访对象/层级" ? [{ label: "输出成果", value: "拜访目的与预期成果" }] : []),
  ],
}))

export const itoSalesWeeklyTaskSampleFields = taskExamples.map((task, index) => ({
  label: `任务 ${index + 1}`,
  rows: [
    { label: "维度", value: task.customer },
    { label: "工作任务", value: task.task },
    { label: "主要工作指引", value: task.work || "（暂无填写）" },
    ...(task.work === "拜访对象/层级" ? [{ label: "输出成果", value: "拜访目的与预期成果" }] : []),
  ],
}))

export const itoSalesWeeklyTaskSample = taskExamples
  .map((task, index) => [
    `任务 ${index + 1}`,
    `维度：${task.customer}`,
    `工作任务：${task.task || "（暂无填写）"}`,
    `主要工作指引：${task.work || "（暂无填写）"}`,
    ...(task.work === "拜访对象/层级" ? ["输出成果：拜访目的与预期成果"] : []),
  ].join("\n"))
  .join("\n\n")
