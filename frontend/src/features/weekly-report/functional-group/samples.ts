import { functionalTaskTemplates as functionalWeeklyTaskExamples } from "./task-templates"

/** 职能组模板沿用交付模板的月度目标样式，内容可由职能组按月调整。 */
export const functionalMonthlyPlanSample = `2月度目标
1、净增？？人
1）新增需求：？个
2）增量入职人数：？人
3）流失控制人数：？人
4）离职替补人数：？人
2、成本控制？？元
3、回款：？？万元`

export const functionalMonthlyPlanSampleFields = [
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



/** 工作任务样例不展示客户字段，其余内容完整保留交付模板原文。 */
export const functionalWeeklyTaskSample = functionalWeeklyTaskExamples
  .flatMap(({ task, work }) => [
    `工作任务：${task}`,
    `主要工作内容：${work}`,
  ])
  .join("\n\n")

export const functionalWeeklyTaskSampleFields = functionalWeeklyTaskExamples.map(
  ({ task, work }, index) => ({
    label: `任务 ${index + 1}`,
    rows: [
      { label: "工作任务", value: task },
      { label: "主要工作内容", value: work },
    ],
  }),
)
