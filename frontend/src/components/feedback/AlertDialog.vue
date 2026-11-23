<script setup lang="ts">
import BaseDialog from "@/components/overlay/BaseDialog.vue"

withDefaults(
  defineProps<{
    open: boolean
    title: string
    message: string
    closeLabel?: string
  }>(),
  { closeLabel: "知道了" },
)

const emit = defineEmits<{
  close: []
}>()
</script>

<template>
  <BaseDialog :open="open" :title="title" width="480px" @close="emit('close')">
    <p class="alert-dialog-message" role="alert">{{ message }}</p>

    <template #actions>
      <button class="primary-button" type="button" @click="emit('close')">
        {{ closeLabel }}
      </button>
    </template>
  </BaseDialog>
</template>

<style scoped>
.alert-dialog-message {
  margin: 0;
  padding: 1rem 1.1rem;
  border: 1px solid rgba(224, 148, 31, 0.72);
  border-radius: 14px;
  color: #83540d;
  background: #fff6df;
  font-size: 1rem;
  line-height: 1.65;
}

.primary-button {
  min-height: 42px;
  padding: 0.55rem 1.25rem;
  border: 1px solid transparent;
  border-radius: 12px;
  color: #fff;
  background: var(--accent);
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}
</style>
