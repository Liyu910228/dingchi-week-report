import { deliveryAssistantTaskTemplates } from "./task-templates"

/** 交付助理 Excel 模板中的月度目标样例（原文保留换行）。 */
const monthlyPlanBody = `1、流失控制人数：？人：
1）主动离职：？人；
2）客户释放：？人；
2、离职替补人数：？人，空岗人日：？人日
3、存量收入流失：？元；存量利润流失：？元
4、成本控制：？元`

const monthlyPlanSampleValue = monthlyPlanBody

export const deliveryAssistantMonthlyPlanSample = monthlyPlanSampleValue

export const deliveryAssistantMonthlyPlanSampleFields = [
  {
    label: "总体目标",
    value: monthlyPlanSampleValue,
  },
] as const



/** 周任务样例完整呈现 Excel 中 A 客户的 12 条任务和对应工作内容。 */
export const deliveryAssistantWeeklyTaskSample = [
  "客户：A客户",
  ...deliveryAssistantTaskTemplates.flatMap(({ task, work }) => [
    `工作任务：${task}`,
    `主要工作内容：${work || "（暂无填写）"}`,
  ]),
].join("\n\n")

export const deliveryAssistantWeeklyTaskSampleFields = [
  { label: "客户", value: "A客户" },
  ...deliveryAssistantTaskTemplates.map(({ task, work }, index) => ({
    label: `任务 ${index + 1}`,
    rows: [
      { label: "工作任务", value: task },
      { label: "主要工作内容", value: work || "（暂无填写）" },
    ],
  })),
] as const
