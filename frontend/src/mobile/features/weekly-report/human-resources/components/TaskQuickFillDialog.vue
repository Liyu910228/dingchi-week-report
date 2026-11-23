<script setup lang="ts">
import { ref, watch } from "vue"
import BaseDialog from "@/mobile/components/overlay/BaseDialog.vue"
import { reportFormValidity } from "@/utils/form-validation"
import type { HumanResourcesTemplate } from "../task-templates"
const props = defineProps<{ open: boolean; monthly?: boolean; templates: readonly HumanResourcesTemplate[] }>()
const emit = defineEmits<{ close: []; confirm: [module: string, indexes: number[]] }>()
const selected = ref<number[]>([])
const formElement = ref<HTMLFormElement | null>(null)
const inputs = ref<HTMLInputElement[]>([])
watch(() => props.open, () => { selected.value = [] })
function clear() { inputs.value.forEach(input => input.setCustomValidity("")) }
function confirm() {
  clear()
  inputs.value[0]?.setCustomValidity(selected.value.length ? "" : "请至少选择一项工作事项。")
  if (reportFormValidity(formElement.value)) emit("confirm", "", [...selected.value].sort((a, b) => a - b))
}
</script>

<template>
  <BaseDialog :open="open" title="选择人资工作事项" width="960px" height="90vh" @close="emit('close')">
    <form id="human-resources-quick-fill" ref="formElement" class="quick-fill" novalidate @submit.prevent="confirm">
      <div class="selection-heading"><strong>选择工作事项（已选 {{ selected.length }} / {{ templates.length }}）</strong><button class="link-button" type="button" @click="selected = selected.length === templates.length ? [] : templates.map((_, index) => index); clear()">{{ selected.length === templates.length ? '取消全选' : '全选' }}</button></div>
      <label v-for="(item, index) in templates" :key="index" class="template-option" :class="{ selected: selected.includes(index) }">
        <input ref="inputs" v-model="selected" type="checkbox" :value="index" :aria-label="`选择事项 ${index + 1}`" @change="clear" />
        <span class="template-content">
          <span class="template-section"><span class="section-label">模块</span><strong class="section-text">{{ item.dimension }}</strong></span>
          <span class="template-section task-section"><span class="section-label">工作任务</span><strong class="section-text">{{ item.task }}</strong></span>
          <span class="template-section work-section"><span class="section-label">工作内容</span><span class="section-text">{{ item.work }}</span></span>
        </span>
      </label>
    </form>
    <template #actions><button class="ghost-button" type="button" @click="emit('close')">取消</button><button class="primary-button" type="submit" form="human-resources-quick-fill">确定</button></template>
  </BaseDialog>
</template>
<style scoped src="./TaskQuickFillDialog.css"></style>
