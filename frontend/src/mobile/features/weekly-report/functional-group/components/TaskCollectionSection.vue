<script setup lang="ts">
import DeliveryTaskCollectionSection from "@/mobile/features/weekly-report/components/DeliveryTaskCollectionSection.vue"
import type { DeliveryTaskCollectionProps } from "@/mobile/features/weekly-report/composables/useDeliveryTaskCollection"
import type { FunctionalTaskDraft } from "@/mobile/features/weekly-report/functional-group/types"
import { functionalTaskTemplates } from "@/mobile/features/weekly-report/functional-group/task-templates"
import { functionalTaskFieldDefinitions } from "@/mobile/features/weekly-report/functional-group/types"
import { functionalWeeklyTaskSample, functionalWeeklyTaskSampleFields } from "@/mobile/features/weekly-report/functional-group/samples"
defineProps<DeliveryTaskCollectionProps>()
const emit = defineEmits<{ "update:tasks": [tasks: FunctionalTaskDraft[]] }>()
</script>
<template>
  <DeliveryTaskCollectionSection :title="title" :mode="mode" :tasks="tasks" :default-owner-id="defaultOwnerId" :owner-name="ownerName"
    :field-definitions="fieldDefinitions?.length ? fieldDefinitions : functionalTaskFieldDefinitions"
    :include-customer="false" column-preference-key="functional_group_v1" :templates="functionalTaskTemplates"
    :sample-content="functionalWeeklyTaskSample" :sample-fields="functionalWeeklyTaskSampleFields"
    @update:tasks="emit('update:tasks', $event)" />
</template>
