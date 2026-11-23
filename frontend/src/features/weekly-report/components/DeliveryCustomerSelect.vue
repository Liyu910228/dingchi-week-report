<script setup lang="ts">
import { computed, onMounted, ref } from "vue"

import SearchableSelect from "@/components/form/SearchableSelect.vue"
import { listDictionaryItems } from "@/features/dictionary/api"
import type { DictionaryItem } from "@/features/dictionary/types"

const props = defineProps<{ modelValue: string; readonly?: boolean; required?: boolean; teleportMenu?: boolean }>()
const emit = defineEmits<{ "update:modelValue": [value: string] }>()
const originalValue = props.modelValue
const customers = ref<DictionaryItem[]>([])
const isLoading = ref(false)
const errorMessage = ref("")
const validityMessage = computed(() => {
  if (isLoading.value) return "客户列表正在加载，请稍后再确认。"
  if (errorMessage.value) return "客户列表加载失败，请重试后选择客户。"
  if (props.required && !props.modelValue.trim()) return "请选择客户。"
  if (props.modelValue && !validate()) return "请选择有效的客户。"
  return ""
})
const options = computed(() => {
  const items = customers.value.map((item) => ({ value: item.dict_name, label: item.dict_name, description: item.dict_code, disabled: false }))
  if (props.modelValue && !items.some((item) => item.value === props.modelValue)) {
    items.push({ value: props.modelValue, label: props.modelValue, description: "历史客户", disabled: true })
  }
  return items
})

async function load() {
  isLoading.value = true
  errorMessage.value = ""
  try {
    customers.value = (await listDictionaryItems("customer")).items
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "客户列表加载失败，请重试。"
  } finally {
    isLoading.value = false
  }
}

function validate() {
  return !isLoading.value && !errorMessage.value && Boolean(props.modelValue)
    && (customers.value.some((item) => item.dict_name === props.modelValue) || props.modelValue === originalValue)
}

defineExpose({ validate })
onMounted(() => { if (!props.readonly) void load() })
</script>

<template>
  <div class="delivery-customer-select">
    <input v-if="readonly" :value="modelValue" readonly aria-label="客户" />
    <template v-else>
      <SearchableSelect
        :teleport-menu="teleportMenu"
        :model-value="modelValue"
        :options="options"
        :options-disabled="isLoading || Boolean(errorMessage)"
        :validation-message="validityMessage"
        placeholder="请选择客户，可输入名称或编号搜索"
        aria-label="客户"
        @update:model-value="emit('update:modelValue', String($event))"
      />
      <small v-if="isLoading" aria-live="polite">正在加载客户…</small>
      <small v-else-if="errorMessage" role="alert">{{ errorMessage }} <button type="button" @click="load">重试</button></small>
      <small v-else-if="!customers.length">暂无启用客户，请在系统设置的客户管理中维护。</small>
    </template>
  </div>
</template>

<style scoped src="./DeliveryCustomerSelect.css"></style>
