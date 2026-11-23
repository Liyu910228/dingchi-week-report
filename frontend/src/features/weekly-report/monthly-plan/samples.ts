import { monthlyPlanScopeLabel } from "./template-fields"

import { deliveryAssistantWeeklyTaskSampleFields } from "../delivery-assistant/samples"
import { deliveryWeeklyTaskSampleFields } from "../delivery-specialist/samples"
import { functionalWeeklyTaskSampleFields } from "../functional-group/samples"
import { innovationSalesWeeklyTaskSampleFields } from "../innovation-sales/samples"
import { itoSalesMonthlyTaskSampleFields } from "../ito-sales/samples"
import { recruitmentMonthlyTaskSampleFields } from "../recruitment/samples"

interface SampleField {
  label: string
  value?: string
  rows?: ReadonlyArray<{ label: string; value: string }>
}

// 当前填写样例仍由前端模板常量维护；按各模板周期选用原文，仅展示月度计划需要的字段。
const samples: Record<string, readonly SampleField[]> = {
  delivery_specialist_v1: deliveryWeeklyTaskSampleFields,
  delivery_assistant_v1: deliveryAssistantWeeklyTaskSampleFields,
  recruitment_v1: recruitmentMonthlyTaskSampleFields,
  ito_sales_v1: itoSalesMonthlyTaskSampleFields,
  innovation_sales_v1: innovationSalesWeeklyTaskSampleFields,
  functional_group_v1: functionalWeeklyTaskSampleFields,
}

export function monthlyPlanSampleFields(templateCode: string): SampleField[] {
  const fields = samples[templateCode] || []
  const scopeLabel = monthlyPlanScopeLabel(templateCode)
  const customer = fields.find((field) => field.label === "客户")?.value || "A客户"
  return fields.filter((field) => field.rows?.some((row) => row.label === "工作任务"))
    .map((field, index) => {
      const scopeValue = field.rows?.find((row) => row.label === scopeLabel)?.value
        || (scopeLabel === "维度" ? "总体目标" : customer)
      return {
        label: `计划 ${index + 1}`,
        rows: [
          ...(scopeLabel ? [{ label: scopeLabel, value: scopeValue }] : []),
          { label: "工作任务", value: field.rows?.find((row) => row.label === "工作任务")?.value || "" },
          ...(["delivery_specialist_v1", "delivery_assistant_v1", "recruitment_v1", "ito_sales_v1", "innovation_sales_v1", "functional_group_v1"].includes(templateCode) ? [{ label: "主要工作内容", value: field.rows?.find(row => ["主要工作内容", "主要工作指引"].includes(row.label))?.value || "" }] : []),
        ],
      }
    })
}
