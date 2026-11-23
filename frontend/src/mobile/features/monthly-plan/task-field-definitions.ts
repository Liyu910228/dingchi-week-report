import { deliveryTaskFieldDefinitions, type DeliveryTaskFieldDefinition } from "@/mobile/features/weekly-report/delivery-specialist/types"
import { deliveryAssistantTaskFieldDefinitions } from "@/mobile/features/weekly-report/delivery-assistant/types"
import { recruitmentTaskFieldDefinitions } from "@/mobile/features/weekly-report/recruitment/types"
import { itoSalesTaskFieldDefinitions } from "@/mobile/features/weekly-report/ito-sales/types"
import { innovationSalesTaskFieldDefinitions } from "@/mobile/features/weekly-report/innovation-sales/types"
import { functionalTaskFieldDefinitions } from "@/mobile/features/weekly-report/functional-group/types"
import { humanResourcesTaskFieldDefinitions } from "@/mobile/features/weekly-report/human-resources/types"

/** 复用各周报模板的字段全集，名称、顺序和可选范围保持一致。 */
export type MonthlyTaskFieldDefinition = Omit<DeliveryTaskFieldDefinition, "code"> & { code: DeliveryTaskFieldDefinition["code"] | "dimension" }
export const monthlyTaskFieldDefinitions: Record<string, MonthlyTaskFieldDefinition[]> = {
  delivery_specialist_v1: deliveryTaskFieldDefinitions,
  delivery_assistant_v1: deliveryAssistantTaskFieldDefinitions,
  recruitment_v1: recruitmentTaskFieldDefinitions,
  ito_sales_v1: itoSalesTaskFieldDefinitions,
  innovation_sales_v1: innovationSalesTaskFieldDefinitions,
  functional_group_v1: functionalTaskFieldDefinitions,
  human_resources_v1: humanResourcesTaskFieldDefinitions,
}
