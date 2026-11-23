<script setup lang="ts">
import {innovationSalesTaskTemplates} from "../task-templates"
import {innovationSalesWeeklyTaskSample,innovationSalesWeeklyTaskSampleFields} from "../samples"
import {emptyInnovationSalesTask} from "../types"
import SalesTaskCollectionSection from "@/mobile/features/weekly-report/components/SalesTaskCollectionSection.vue"
import { innovationSalesTaskFieldDefinitions, type InnovationSalesTaskDraft, type InnovationSalesTaskFieldDefinition } from "@/mobile/features/weekly-report/innovation-sales/types"
defineProps<{ title: string; tasks: InnovationSalesTaskDraft[]; defaultOwnerId?: string; ownerName?: string; fieldDefinitions?: InnovationSalesTaskFieldDefinition[] }>()
const emit = defineEmits<{ "update:tasks": [tasks: InnovationSalesTaskDraft[]] }>()
</script>
<template>
  <SalesTaskCollectionSection :templates="innovationSalesTaskTemplates" :sample-content="innovationSalesWeeklyTaskSample" :sample-fields="innovationSalesWeeklyTaskSampleFields" :task-factory="emptyInnovationSalesTask" template-code="innovation_sales_v1" :title="title" :tasks="tasks" :default-owner-id="defaultOwnerId" :owner-name="ownerName" :field-definitions="fieldDefinitions?.length ? fieldDefinitions : innovationSalesTaskFieldDefinitions" @update:tasks="emit('update:tasks', $event.map(task=>({...task,quality_percent:task.quality_percent ?? 0,completion_rate:task.completion_rate ?? 0})))" />
</template>
