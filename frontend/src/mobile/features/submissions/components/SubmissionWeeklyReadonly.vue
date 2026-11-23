<script setup lang="ts">
import {ref} from "vue"
import CustomerTabsHeader from "./CustomerTabsHeader.vue"
import CustomerTaskTabs from "./CustomerTaskTabs.vue"
import ReportTaskTable from "@/mobile/features/weekly-report/components/ReportTaskTable.vue"
import FullscreenPanel from "@/mobile/components/layout/FullscreenPanel.vue"
import type {SubmissionPart} from "../types"
defineProps<{part:SubmissionPart}>()
const taskTable=ref<InstanceType<typeof ReportTaskTable>|null>(null)
</script>
<template>
<CustomerTaskTabs :tasks="part.detail?.items || []" :customers="part.customers" :name-field="['delivery_specialist_v1','delivery_assistant_v1'].includes(part.template_code)?'customer_name_snapshot':undefined" v-slot="scope"><FullscreenPanel title="本周工作任务" class="dashboard-card weekly-readonly-panel"><template #tabs><CustomerTabsHeader /></template><template #actions><button class="ghost-button" type="button" @click="taskTable?.openColumns()">选择展示字段</button></template><ReportTaskTable ref="taskTable" :show-columns-button="false" :items="scope.tasks" :fields="part.template?.fields" :attachments="part.detail?.attachments" :template-code="part.template_code" :preference-key="part.template_code" :show-customer-tabs="!part.customers.length" /></FullscreenPanel></CustomerTaskTabs>

</template>

<style scoped src="./SubmissionWeeklyReadonly.css"></style>

