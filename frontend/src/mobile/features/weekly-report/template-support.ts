/** 填写页面只允许使用明确实现的模板，未知编码不回退通用表单。 */
export const TEMPLATE_UNAVAILABLE_MESSAGE = "模板未配置，不支持填写"
export const supportedTemplateCodes = [
  "delivery_specialist_v1", "delivery_assistant_v1", "recruitment_v1",
  "ito_sales_v1", "innovation_sales_v1", "functional_group_v1", "human_resources_v1",
] as const
export type SupportedTemplateCode = typeof supportedTemplateCodes[number]
export function isSupportedTemplate(code: string | null | undefined): code is SupportedTemplateCode {
  return supportedTemplateCodes.some(value => value === code)
}
