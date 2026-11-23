<script setup lang="ts">
import BaseDialog from "@/components/overlay/BaseDialog.vue"
import type { Customer } from "@/features/dictionary"

withDefaults(
  defineProps<{
    open: boolean
    customer?: Customer | null
    isDeleting?: boolean
  }>(),
  {
    customer: null,
    isDeleting: false,
  },
)

defineEmits<{
  close: []
  confirm: []
}>()
</script>

<template>
  <BaseDialog
    :busy="isDeleting"
    description="删除后该客户不再出现在客户列表中。"
    :open="open"
    title="删除客户"
    width="480px"
    @close="$emit('close')"
  >
    <div v-if="customer" class="delete-content">
      <p>
        确认删除客户「<strong>{{ customer.dict_name }}</strong>」吗？
      </p>
      <div class="customer-summary">
        <span>客户编号</span>
        <strong>{{ customer.dict_code }}</strong>
      </div>
      <p class="delete-note">历史周报中已引用的客户名称仍会保留，便于追溯。</p>
    </div>

    <template #actions>
      <button class="secondary-button" type="button" :disabled="isDeleting" @click="$emit('close')">
        取消
      </button>
      <button class="danger-button" type="button" :disabled="isDeleting" @click="$emit('confirm')">
        {{ isDeleting ? "删除中…" : "确认删除" }}
      </button>
    </template>
  </BaseDialog>
</template>

<style scoped>
.delete-content p {
  margin: 0 0 0.5rem;
  color: #1f2335;
  font-size: 0.95rem;
}
.customer-summary {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem 0.8rem;
  border-radius: 8px;
  background: #f5f6f9;
  font-size: 0.85rem;
  color: #4a5060;
  margin: 0.6rem 0;
}
.customer-summary strong {
  color: #1f2335;
  font-family: "JetBrains Mono", "SFMono-Regular", Consolas, monospace;
}
.delete-note {
  color: #8a8f9c;
  font-size: 0.82rem;
}
</style>
