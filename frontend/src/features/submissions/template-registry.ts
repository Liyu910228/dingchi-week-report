import {defineAsyncComponent,type Component} from "vue"
/** 注册表只负责装配，各模板的正文和序列化实现互不引用。 */
export const weeklyBodies:Record<string,Component>={
  delivery_specialist_v1:defineAsyncComponent(()=>import("@/features/weekly-report/delivery-specialist/UnifiedWeeklyBody.vue")),
  delivery_assistant_v1:defineAsyncComponent(()=>import("@/features/weekly-report/delivery-assistant/UnifiedWeeklyBody.vue")),
  recruitment_v1:defineAsyncComponent(()=>import("@/features/weekly-report/recruitment/UnifiedWeeklyBody.vue")),
  ito_sales_v1:defineAsyncComponent(()=>import("@/features/weekly-report/ito-sales/UnifiedWeeklyBody.vue")),
  innovation_sales_v1:defineAsyncComponent(()=>import("@/features/weekly-report/innovation-sales/UnifiedWeeklyBody.vue")),
  human_resources_v1:defineAsyncComponent(()=>import("@/features/weekly-report/human-resources/UnifiedWeeklyBody.vue")),
  functional_group_v1:defineAsyncComponent(()=>import("@/features/weekly-report/functional-group/UnifiedWeeklyBody.vue")),
}

export const monthlyBodies:Record<string,Component>={
  delivery_specialist_v1:defineAsyncComponent(()=>import("@/features/weekly-report/delivery-specialist/UnifiedMonthlyBody.vue")),
  delivery_assistant_v1:defineAsyncComponent(()=>import("@/features/weekly-report/delivery-assistant/UnifiedMonthlyBody.vue")),
  recruitment_v1:defineAsyncComponent(()=>import("@/features/weekly-report/recruitment/UnifiedMonthlyBody.vue")),
  ito_sales_v1:defineAsyncComponent(()=>import("@/features/weekly-report/ito-sales/UnifiedMonthlyBody.vue")),
  innovation_sales_v1:defineAsyncComponent(()=>import("@/features/weekly-report/innovation-sales/UnifiedMonthlyBody.vue")),
  functional_group_v1:defineAsyncComponent(()=>import("@/features/weekly-report/functional-group/UnifiedMonthlyBody.vue")),
  human_resources_v1:defineAsyncComponent(()=>import("@/features/weekly-report/human-resources/UnifiedMonthlyBody.vue")),
}
