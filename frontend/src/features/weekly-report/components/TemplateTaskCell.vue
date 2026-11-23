<script setup lang="ts">
import { computed } from "vue"
import type { EditableTask } from "@/features/weekly-report/task-editing"
import { previewTaskTemplate, renderTaskTemplate } from "@/features/weekly-report/task-texts"
const props = withDefaults(defineProps<{ task: Pick<EditableTask, "task_name" | "task_template" | "task_values">; label?: string }>(), { label: "工作任务" })
const parts = computed(() => (props.task.task_template || props.task.task_name).split(/[?？]/))
const preview = computed(() => previewTaskTemplate(
  props.task.task_template || props.task.task_name, props.task.task_values || [],
))
const emit = defineEmits<{ patch: [value: Partial<EditableTask>] }>()
function change(index: number, event: Event) {
  const values = [...(props.task.task_values || [])]
  values[index] = (event.target as HTMLInputElement).value
  emit("patch", { task_values: values, task_name: renderTaskTemplate(props.task.task_template || "", values) })
}
</script>
<template>
  <div class="template-task-text user-content" tabindex="0" :aria-label="`编辑${label}占位值`">
    <span class="template-task-preview">{{ preview }}</span>
    <span class="template-task-editor"><template v-for="(part, index) in parts" :key="index"><span>{{ part }}</span><input v-if="index < parts.length - 1" :value="task.task_values?.[index] || ''" maxlength="256" :aria-label="`${label}第${index + 1}个占位值`" placeholder="?" @input="change(index, $event)" /></template></span>
  </div>
</template>
<style scoped src="./TemplateTaskCell.css"></style>
