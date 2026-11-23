<script setup lang="ts">
import {deliveryTaskTemplates} from "./task-templates"
import {deliveryWeeklyTaskSample,deliveryWeeklyTaskSampleFields} from "./samples"
import {watch} from "vue"
import { useDeliveryReportForm, hydrateReportItem } from "./useDeliveryReportForm"
import type {SubmissionPart} from "@/mobile/features/submissions/types"
import type {ReportPayload} from "@/mobile/features/weekly-report/types"
import CustomerTaskTabs from "@/mobile/features/submissions/components/CustomerTaskTabs.vue"
import TaskCollectionSection from "@/mobile/features/weekly-report/components/DeliveryTaskCollectionSection.vue"
const props=defineProps<{part:SubmissionPart;periodStart:string}>()
const emit=defineEmits<{"update:payload":[value:ReportPayload]}>()
const form=useDeliveryReportForm(()=>props.part.id || "")
watch(()=>props.part,part=>{
 Object.assign(form.report,{id:part.id || "",period_start:props.periodStart,period_end:part.detail?.report.period_end || "",month_key:props.periodStart.slice(0,7),summary:part.payload.summary || ""})
 form.weeklyTasks.value=(part.detail?.items || []).map(item=>hydrateReportItem(item,(part.detail?.attachments || []).filter(a=>a.relation_sub_id===item.id)))
 form.dailyTasks.value=part.detail?.daily_tasks || []
 const fields=part.template?.fields || []
 form.taskFields.value=form.taskFields.value.map(field=>{const configured=fields.find(value=>value.field_code===field.code);return configured?{...field,label:configured.label,sort_order:configured.sort_order,default_visible:configured.default_visible}:field})
 form.isLoading.value=false
},{immediate:true})
watch(()=>props.periodStart,value=>form.setPeriodStart(value),{immediate:true})
watch(()=>form.buildPayload(),payload=>emit("update:payload",payload),{deep:true,immediate:true})
</script>
<template>
 <CustomerTaskTabs :tasks="form.weeklyTasks.value" :customers="part.customers" name-field="customer_name" @update:tasks="form.weeklyTasks.value=$event" v-slot="scope">
  <TaskCollectionSection :tasks="scope.tasks" @update:tasks="scope.update($event)" title="本周工作任务" :default-owner-id="form.authStore.user?.id || ''" :owner-name="form.authStore.user?.display_name || ''" :field-definitions="form.taskFields.value"  :templates="deliveryTaskTemplates" :sample-content="deliveryWeeklyTaskSample" :sample-fields="deliveryWeeklyTaskSampleFields" mode="weekly" column-preference-key="delivery_specialist_v1" />
 </CustomerTaskTabs>
</template>

