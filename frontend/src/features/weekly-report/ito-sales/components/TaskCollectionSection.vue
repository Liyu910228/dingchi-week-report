<script setup lang="ts">
import {itoSalesTaskTemplates} from "../task-templates"
import {itoSalesWeeklyTaskSample,itoSalesWeeklyTaskSampleFields} from "../samples"
import {emptyItoSalesTask} from "../types"
import SalesTaskCollectionSection from "@/features/weekly-report/components/SalesTaskCollectionSection.vue"
import { itoSalesTaskFieldDefinitions, type ItoSalesTaskDraft, type ItoSalesTaskFieldDefinition } from "@/features/weekly-report/ito-sales/types"
defineProps<{ title: string; tasks: ItoSalesTaskDraft[]; defaultOwnerId?: string; ownerName?: string; fieldDefinitions?: ItoSalesTaskFieldDefinition[] }>()
const emit = defineEmits<{ "update:tasks": [tasks: ItoSalesTaskDraft[]] }>()
</script>
<template>
  <SalesTaskCollectionSection :templates="itoSalesTaskTemplates" :sample-content="itoSalesWeeklyTaskSample" :sample-fields="itoSalesWeeklyTaskSampleFields" :task-factory="emptyItoSalesTask" template-code="ito_sales_v1" :title="title" :tasks="tasks" :default-owner-id="defaultOwnerId" :owner-name="ownerName" :field-definitions="fieldDefinitions?.length ? fieldDefinitions : itoSalesTaskFieldDefinitions" @update:tasks="emit('update:tasks', $event.map(task=>({...task,quality_percent:task.quality_percent ?? 0,completion_rate:task.completion_rate ?? 0})))" />
</template>
