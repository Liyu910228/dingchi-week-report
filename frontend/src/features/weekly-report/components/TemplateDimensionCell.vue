<script setup lang="ts">
import TemplateTaskCell from "./TemplateTaskCell.vue"
import type { TaskTextMetadata } from "../task-texts"
import type { EditableTask } from "../task-editing"
defineProps<{ task: TaskTextMetadata & { dimension?: string } }>()
const emit = defineEmits<{ patch: [value: Partial<EditableTask>] }>()
</script>
<template>
  <TemplateTaskCell label="维度" :task="{ task_name: task.dimension || '', task_template: task.dimension_template, task_values: task.dimension_values }"
    @patch="emit('patch', { dimension: $event.task_name, dimension_values: $event.task_values })" />
</template>
