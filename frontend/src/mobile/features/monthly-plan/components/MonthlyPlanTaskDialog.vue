<script setup lang="ts">
import {inject} from "vue"
import {customerScopeKey} from "@/mobile/features/submissions/customer-scope"
const customerScope=inject(customerScopeKey,undefined)
import { computed, nextTick, ref, watch } from "vue"
import { isSupportedTemplate } from "@/mobile/features/weekly-report/template-support"

import DeliveryCustomerSelect from "@/mobile/features/weekly-report/components/DeliveryCustomerSelect.vue"
import { monthlyPlanScopeLabel, usesConfiguredCustomers } from "@/mobile/features/weekly-report/monthly-plan/template-fields"
import { clearFieldValidity, reportFormValidity } from "@/utils/form-validation"
import BaseDialog from "@/mobile/components/overlay/BaseDialog.vue"
import type { MonthlyPlanTask, MonthlyPlanTaskPayload } from "@/mobile/features/weekly-report/monthly-plan/types"
import TaskTemplatePopover from "@/mobile/features/weekly-report/components/TaskTemplatePopover.vue"
import type {TaskTemplateOption} from "@/mobile/features/weekly-report/task-editing"

const props = defineProps<{ open: boolean; task: MonthlyPlanTask | null; readonly?: boolean; templateCode?: string;templates?:readonly TaskTemplateOption[] }>()
const emit = defineEmits<{ close: []; save: [task: MonthlyPlanTaskPayload, action: "close" | "next"] }>()
const customerSelect = ref<InstanceType<typeof DeliveryCustomerSelect> | null>(null)
const scopeLabel = computed(() => monthlyPlanScopeLabel(props.templateCode || ""))
const configuredCustomers = computed(() => usesConfiguredCustomers(props.templateCode || ""))
const customerName = ref("")
const workTask = ref("")
const workContent = ref("")
const input = ref<HTMLTextAreaElement | null>(null)
const formElement = ref<HTMLFormElement | null>(null)
const pickerOpen = ref(false)
const pickerTrigger = ref<HTMLButtonElement | null>(null)
const anchor = ref<HTMLElement | null>(null)
const selectedTemplate = ref("")
const templates = computed(() => props.templates || [])
function togglePicker() {
  anchor.value = formElement.value?.closest<HTMLElement>('[role="dialog"]') || null
  pickerOpen.value = !pickerOpen.value
}
async function fillTemplate(index: number) {
  const template = templates.value[index]
  if (!template) return
  workTask.value = template.task
  workContent.value = template.work
  if (props.templateCode === "recruitment_v1" && !customerName.value.trim()) customerName.value = templates.value[index]?.dimension || ""
  selectedTemplate.value = String(index)
  pickerOpen.value = false
  await nextTick()
  input.value?.dispatchEvent(new Event("input", { bubbles: true }))
  input.value?.focus()
}

watch(() => [props.open, props.task] as const, () => {
  pickerOpen.value = false
  selectedTemplate.value = ""
  if (!props.open) return
  customerName.value = props.task?.scope_name || customerScope?.name.value || ""
  workTask.value = props.task?.work_task || ""
  workContent.value = props.task?.work_content || ""
  if (!props.readonly) void nextTick(() => input.value?.focus())
}, { immediate: true })

function save(action: "close" | "next") {
  if (!reportFormValidity(formElement.value)) return
  const value = workTask.value.trim()
  emit("save", {
    scope_name: scopeLabel.value ? customerName.value.trim() : "",
    work_task: value,
    work_content: workContent.value.trim(),
  }, action)
  if (action === "next") {
    workTask.value = ""
    workContent.value = ""
    void nextTick(() => input.value?.focus())
  }
}
</script>

<template>
  <BaseDialog
    :open="open && (readonly || isSupportedTemplate(templateCode))"
    :title="readonly ? '月度计划详情' : task ? '编辑月度计划' : '新增月度计划'"
    width="680px"
    @close="emit('close')"
  >
    <form ref="formElement" novalidate @input.capture="clearFieldValidity" @change.capture="clearFieldValidity" id="monthly-plan-task-form" class="monthly-task-form" @submit.prevent="save('close')">
      <template v-if="scopeLabel">
        <label for="monthly-plan-customer">{{ scopeLabel }}<span v-if="!readonly" class="required"> *</span></label>
        <DeliveryCustomerSelect v-if="configuredCustomers" ref="customerSelect" v-model="customerName" :readonly="readonly" required />
        <input class="user-content" v-else id="monthly-plan-customer" v-model="customerName" maxlength="255" :readonly="readonly" :required="!readonly" :placeholder="`请输入${scopeLabel}`" />
      </template>
      <div class="monthly-task-field-heading"><label for="monthly-plan-work-task">工作任务<span v-if="!readonly" class="required"> *</span></label><button v-if="!readonly && ['delivery_specialist_v1', 'recruitment_v1'].includes(templateCode || '')" ref="pickerTrigger" class="monthly-template-button" type="button" :aria-expanded="pickerOpen" aria-haspopup="dialog" @click="togglePicker">选择模板</button></div>
      <textarea class="user-content"
        id="monthly-plan-work-task"
        ref="input"
        v-model="workTask"
        rows="6"
        :readonly="readonly"
        :required="!readonly"
        placeholder="请输入本月计划开展的工作任务"
      />
      <label for="monthly-plan-work-content">工作内容</label>
      <textarea class="user-content" id="monthly-plan-work-content" v-model="workContent" rows="6" maxlength="10000" :readonly="readonly" placeholder="请输入工作内容" />
    </form>
    <template #actions>
      <button class="ghost-button" type="button" @click="emit('close')">
        {{ readonly ? "关闭" : "取消" }}
      </button>
      <template v-if="!readonly">
        <button class="ghost-button" type="submit" form="monthly-plan-task-form">确定</button>
        <button v-if="!task" class="ghost-button" type="button" @click="save('next')">确定并继续添加</button>
      </template>
    </template>
  </BaseDialog>
  <TaskTemplatePopover :open="open && pickerOpen" :anchor="anchor" :trigger="pickerTrigger" :selected="selectedTemplate" :templates="templates" @close="pickerOpen = false" @select="fillTemplate" />
</template>

<style scoped src="./MonthlyPlanTaskDialog.css"></style>
