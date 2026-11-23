<script setup lang="ts">
import ExamplePreviewButton from "@/components/feedback/ExamplePreviewButton.vue"
import {humanResourcesMonthlyPlanSampleFields} from "./samples"
import type {SubmissionPart,MonthlyPayload} from "@/features/submissions/types"
import CustomerTaskTabs from "@/features/submissions/components/CustomerTaskTabs.vue"
import MonthlyPlanTaskPanel from "./components/MonthlyPlanPanel.vue"
const props=defineProps<{part:SubmissionPart;monthKey:string;readonly?:boolean;progressEditable?:boolean}>()
const emit=defineEmits<{"update:payload":[value:MonthlyPayload]}>()
</script>
<template>
<section class="dashboard-card goal-card"><header class="goal-heading"><h2>月度目标<span v-if="!readonly" class="required" aria-hidden="true"> *</span></h2><ExamplePreviewButton v-if="!readonly" content="" :fields="humanResourcesMonthlyPlanSampleFields" panel-title="月度目标填写样例" /></header><p v-if="readonly" class="goal-text user-content">{{part.payload.summary || '—'}}</p><textarea class="user-content" aria-label="月度目标" aria-required="true" required placeholder="请输入本月工作目标" v-else :value="part.payload.summary" rows="4" maxlength="10000" @input="emit('update:payload',{...props.part.payload,summary:($event.target as HTMLTextAreaElement).value})" /></section>
<CustomerTaskTabs :tasks="part.payload.tasks || []" :customers="part.customers" @update:tasks="emit('update:payload',{...props.part.payload,tasks:$event})" v-slot="scope">
<MonthlyPlanTaskPanel :tasks="scope.tasks" @update:tasks="scope.update($event)" :month-key="monthKey" template-code="human_resources_v1" :readonly="readonly" :progress-editable="progressEditable" />
</CustomerTaskTabs>
</template>
<style scoped src="./UnifiedMonthlyBody.css"></style>
