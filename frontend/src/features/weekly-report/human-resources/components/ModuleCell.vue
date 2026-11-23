<script setup lang="ts">
import TemplateTaskCell from "@/features/weekly-report/components/TemplateTaskCell.vue"
import type { EditableTask } from "@/features/weekly-report/task-editing"
import type { TaskTextMetadata } from "@/features/weekly-report/task-texts"
defineProps<{ task: TaskTextMetadata & { dimension?: string } }>()
const emit = defineEmits<{ patch: [value: Partial<EditableTask>] }>()
</script>
<template><TemplateTaskCell label="模块" :task="{ task_name: task.dimension || '', task_template: task.dimension_template, task_values: task.dimension_values }" @patch="emit('patch', { dimension: $event.task_name, dimension_values: $event.task_values })" /></template>
