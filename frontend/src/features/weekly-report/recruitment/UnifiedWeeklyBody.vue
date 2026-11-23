<script setup lang="ts">
import {watch} from "vue"
import { useRecruitmentReportForm, hydrateReportItem } from "./useRecruitmentReportForm"
import type {SubmissionPart} from "@/features/submissions/types"
import type {ReportPayload} from "@/features/weekly-report/types"
import CustomerTaskTabs from "@/features/submissions/components/CustomerTaskTabs.vue"
import TaskCollectionSection from "@/features/weekly-report/recruitment/components/TaskCollectionSection.vue"
const props=defineProps<{part:SubmissionPart;periodStart:string}>()
const emit=defineEmits<{"update:payload":[value:ReportPayload]}>()
const form=useRecruitmentReportForm(()=>props.part.id || "")
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
 <CustomerTaskTabs :tasks="form.weeklyTasks.value" :customers="part.customers"  @update:tasks="form.weeklyTasks.value=$event" v-slot="scope">
  <TaskCollectionSection :tasks="scope.tasks" @update:tasks="scope.update($event)" title="本周工作任务" :default-owner-id="form.authStore.user?.id || ''" :owner-name="form.authStore.user?.display_name || ''" :field-definitions="form.taskFields.value"  />
 </CustomerTaskTabs>
</template>

