import { recruitmentMonthlyGoal, recruitmentMonthlyTaskTemplates, recruitmentTaskTemplates } from "./task-templates"

export const recruitmentMonthlyPlanSample = recruitmentMonthlyGoal
export const recruitmentMonthlyPlanSampleFields = [{ label: "总体目标", value: recruitmentMonthlyGoal }] as const
function taskSampleFields(templates: ReadonlyArray<(typeof recruitmentTaskTemplates)[number]>) {
  return templates.map((item, index) => ({
  label: `任务 ${index + 1}`,
  rows: [
    { label: "维度", value: item.dimension },
    { label: "工作任务", value: item.task },
    { label: "主要工作内容", value: item.work },
  ],
  }))
}
export const recruitmentWeeklyTaskSampleFields = taskSampleFields(recruitmentTaskTemplates)
export const recruitmentMonthlyTaskSampleFields = taskSampleFields(recruitmentMonthlyTaskTemplates)
export const recruitmentWeeklyTaskSample = recruitmentWeeklyTaskSampleFields
  .flatMap(item => [item.label, ...item.rows.map(row => `${row.label}：${row.value}`)]).join("\n")
