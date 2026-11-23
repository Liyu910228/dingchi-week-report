<script setup lang="ts">
import { customerScopeKey } from "@/features/submissions/customer-scope"
import { inject, ref, watch } from "vue"
import BaseDialog from "@/components/overlay/BaseDialog.vue"
import DeliveryCustomerSelect from "@/features/weekly-report/components/DeliveryCustomerSelect.vue"
import { reportFormValidity } from "@/utils/form-validation"

import type { TaskTemplateOption } from "@/features/weekly-report/task-editing"

const props = withDefaults(defineProps<{ open: boolean; monthly?: boolean; recruitment?: boolean; sales?: boolean; scopeLess?: boolean; customerLabel?: string; templates?: readonly TaskTemplateOption[] }>(), { templates: () => [], customerLabel: "客户" })
const emit = defineEmits<{ close: []; confirm: [customer: string, indexes: number[]] }>()
const customerScope = inject(customerScopeKey, undefined)
const customer = ref("")
const selected = ref<number[]>([])
const formElement = ref<HTMLFormElement | null>(null)
const taskInputs = ref<HTMLInputElement[]>([])
watch(() => props.open, (open) => {
  if (open) { customer.value = customerScope?.name.value || ""; selected.value = [] }
})
function clearTaskValidity() {
  taskInputs.value.forEach(input => input.setCustomValidity(""))
}
function toggleAll() {
  selected.value = selected.value.length === props.templates.length ? [] : props.templates.map((_, index) => index)
  clearTaskValidity()
}
function confirm() {
  clearTaskValidity()
  taskInputs.value[0]?.setCustomValidity(selected.value.length ? "" : "请至少选择一项工作任务。")
  if (!reportFormValidity(formElement.value)) return
  emit("confirm", customer.value, [...selected.value].sort((a, b) => a - b))
}
</script>

<template>
  <BaseDialog :open="open" title="快速填写任务" width="960px" height="90vh" @close="emit('close')">
    <form ref="formElement" id="delivery-quick-fill-form" class="quick-fill" novalidate @submit.prevent="confirm">
      <label v-if="!recruitment && !sales && !scopeLess">客户 <span class="required">*</span></label>
      <DeliveryCustomerSelect v-if="open && !recruitment && !sales && !scopeLess" v-model="customer" required />
      <div class="selection-heading"><strong>选择工作任务（已选 {{ selected.length }} / {{ templates.length }}）</strong><button class="link-button" type="button" @click="toggleAll">{{ selected.length === templates.length ? '取消全选' : '全选' }}</button></div>
      <label v-for="(item, index) in templates" :key="index" class="template-option" :class="{ selected: selected.includes(index), 'recruitment-option': recruitment }">
        <input ref="taskInputs" v-model="selected" type="checkbox" :value="index" :aria-label="`选择任务 ${index + 1}`" @change="clearTaskValidity" />
        <strong v-if="recruitment" class="dimension-title">{{ item.dimension }}</strong>
        <span class="template-content">
          <span v-if="sales" class="template-section"><span class="section-label">{{ customerLabel }}</span><strong class="section-text">{{ item.customer }}</strong></span>
          <span v-if="item.dimension && !recruitment" class="template-section"><span class="section-label">维度</span><strong class="section-text">{{ item.dimension }}</strong></span>
          <span class="template-section task-section"><span class="section-label">工作任务</span><strong class="section-text">{{ item.task }}</strong></span>
          <span class="template-section work-section"><span class="section-label">主要工作内容</span><span class="section-text">{{ item.work }}</span></span>
        </span>
      </label>
    </form>
    <template #actions><button class="ghost-button" type="button" @click="emit('close')">取消</button><button class="primary-button" type="submit" form="delivery-quick-fill-form">确定</button></template>
  </BaseDialog>
</template>

<style scoped src="./TaskQuickFillDialog.css"></style>
