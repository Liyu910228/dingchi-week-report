<script setup lang="ts">
import { nextTick, ref, watch } from "vue"
import BaseDialog from "@/components/overlay/BaseDialog.vue"
import { humanResourcesTaskTemplates } from "../task-templates"
import TaskTemplatePopover from "./TaskTemplatePopover.vue"
import type { TaskTemplateOption } from "@/features/weekly-report/task-editing"
const props = withDefaults(defineProps<{ open: boolean; title: string; value: string; customerLabel?: string; maxLength?: number; templateField?: "task_name" | "work_content" | "dimension" | "customer_name"; templates?: readonly TaskTemplateOption[] }>(), { templates: () => humanResourcesTaskTemplates })
const emit = defineEmits<{ close: []; save: [value: string, templateIndex?: number] }>()
const draft = ref("")
const selectedTemplate = ref("")
const pickerOpen = ref(false)
const formElement = ref<HTMLFormElement | null>(null)
const pickerTrigger = ref<HTMLButtonElement | null>(null)
const anchor = ref<HTMLElement | null>(null)
watch(() => [props.open, props.value, props.templateField], () => {
  pickerOpen.value = false
  if (props.open) { draft.value = props.value; selectedTemplate.value = "" }
}, { immediate: true })
async function fillTemplate(index: number) {
  if (!props.templateField) return
  const template = props.templates[index]
  selectedTemplate.value = String(index)
  if (template) draft.value = props.templateField === "customer_name" ? template.customer || "" : props.templateField === "dimension" ? template.dimension || "" : props.templateField === "task_name" ? template.task : template.work
  pickerOpen.value = false
  await nextTick()
  formElement.value?.querySelector("textarea")?.dispatchEvent(new Event("input", { bubbles: true }))
  pickerTrigger.value?.focus()
}
function togglePicker() {
  anchor.value = formElement.value?.closest<HTMLElement>('[role="dialog"]') || null
  pickerOpen.value = !pickerOpen.value
}
function save() {
  emit("save", draft.value.trim(), props.templateField && selectedTemplate.value !== "" ? Number(selectedTemplate.value) : undefined)
}
</script>
<template>
  <BaseDialog :open="open" :title="`编辑${title}`" width="800px" @close="emit('close')">
    <form id="human-resources-task-text-form" ref="formElement" class="text-field-form" @submit.prevent="save">
      <div class="text-field-heading"><label for="human-resources-task-text">{{ title }}</label><button v-if="templateField" ref="pickerTrigger" type="button" class="template-picker-button" :aria-expanded="pickerOpen" aria-haspopup="dialog" @click="togglePicker">选择模板</button></div>
      <textarea id="human-resources-task-text" v-model="draft" class="text-field-input user-content" :rows="templateField === 'dimension' || templateField === 'customer_name' ? 3 : 10" :maxlength="maxLength" :aria-label="title" />
    </form>
    <template #actions><button class="ghost-button" type="button" @click="emit('close')">取消</button><button class="primary-button" type="submit" form="human-resources-task-text-form">确定</button></template>
  </BaseDialog>
  <TaskTemplatePopover :open="open && pickerOpen" :anchor="anchor" :trigger="pickerTrigger" :selected="selectedTemplate" :templates="templates" :customer-label="customerLabel" @close="pickerOpen = false" @select="fillTemplate" />
</template>
<style scoped src="./TaskTextFieldDialog.css"></style>
