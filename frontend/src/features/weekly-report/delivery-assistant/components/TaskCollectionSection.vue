<script setup lang="ts">
import DeliveryTaskCollectionSection from "@/features/weekly-report/components/DeliveryTaskCollectionSection.vue"
import { deliveryAssistantWeeklyTaskSample, deliveryAssistantWeeklyTaskSampleFields } from "@/features/weekly-report/delivery-assistant/samples"
import { deliveryAssistantTaskTemplates } from "@/features/weekly-report/delivery-assistant/task-templates"
import { emptyDeliveryAssistantTask, deliveryAssistantTaskFieldDefinitions, type DeliveryAssistantTaskDraft, type DeliveryAssistantTaskFieldDefinition } from "@/features/weekly-report/delivery-assistant/types"
import type { TaskDraft } from "@/features/weekly-report/task-draft"
const props = defineProps<{ title: string; tasks: DeliveryAssistantTaskDraft[]; defaultOwnerId?: string; ownerName?: string; fieldDefinitions?: DeliveryAssistantTaskFieldDefinition[] }>()
const emit = defineEmits<{ "update:tasks": [tasks: DeliveryAssistantTaskDraft[]] }>()
function update(tasks: TaskDraft[]) {
  emit("update:tasks", tasks.map(task => ({ ...task, quality_percent: task.quality_percent ?? 0, completion_rate: task.completion_rate ?? 0 })))
}
</script>
<template>
  <DeliveryTaskCollectionSection v-bind="props" mode="weekly" column-preference-key="delivery_assistant_v1"
    :field-definitions="fieldDefinitions?.length ? fieldDefinitions : deliveryAssistantTaskFieldDefinitions"
    :sample-content="deliveryAssistantWeeklyTaskSample" :sample-fields="deliveryAssistantWeeklyTaskSampleFields"
    :templates="deliveryAssistantTaskTemplates" :task-factory="emptyDeliveryAssistantTask" @update:tasks="update" />
</template>
