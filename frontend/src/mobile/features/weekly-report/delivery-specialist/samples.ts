import { deliveryTaskTemplates } from "./task-templates"

/**
 * 交付专员 Excel 模板中的原始填写样例。
 * 月度目标对应 D3；周任务对应 A 客户的 C4:D11，保留单元格中的原文和换行。
 */
export const deliveryMonthlyPlanSample = `2月度目标
1、净增？？人
1）新增需求：？个
2）增量入职人数：？人
3）流失控制人数：？人
4）离职替补人数：？人
2、成本控制？？元
3、回款：？？万元`

export const deliveryMonthlyPlanSampleFields = [
  {
    label: "2月度目标",
    value: `1、净增？？人
1）新增需求：？个
2）增量入职人数：？人
3）流失控制人数：？人
4）离职替补人数：？人
2、成本控制？？元
3、回款：？？万元`,
  },
] as const



export const deliveryWeeklyTaskSample = [
  "客户：A客户",
  ...deliveryTaskTemplates.flatMap(({ task, work }) => [
    `工作任务：${task}`,
    `主要工作内容：${work}`,
  ]),
].join("\n\n")

export const deliveryWeeklyTaskSampleFields = [
  { label: "客户", value: "A客户" },
  ...deliveryTaskTemplates.map(({ task, work }, index) => ({
    label: `任务 ${index + 1}`,
    rows: [
      { label: "工作任务", value: task },
      { label: "主要工作内容", value: work },
    ],
  })),
]
