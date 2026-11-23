<script setup lang="ts">
import BaseDialog from "@/components/overlay/BaseDialog.vue"

withDefaults(
  defineProps<{
    open: boolean
    title: string
    message: string
    confirmLabel?: string
    confirmVariant?: "primary" | "danger"
    busy?: boolean
  }>(),
  {
    confirmLabel: "确认",
    confirmVariant: "primary",
    busy: false,
  },
)

const emit = defineEmits<{
  close: []
  confirm: []
}>()
</script>

<template>
  <BaseDialog
    :open="open"
    :title="title"
    width="480px"
    :busy="busy"
    @close="emit('close')"
  >
    <p class="confirm-dialog-message" role="alert">{{ message }}</p>
    <template #actions>
      <button class="secondary-button" type="button" :disabled="busy" @click="emit('close')">
        取消
      </button>
      <button
        :class="confirmVariant === 'danger' ? 'danger-button' : 'primary-button'"
        type="button"
        :disabled="busy"
        @click="emit('confirm')"
      >
        {{ confirmLabel }}
      </button>
    </template>
  </BaseDialog>
</template>

<style scoped>
.confirm-dialog-message {
  margin: 0;
  padding: 1rem 1.1rem;
  border: 1px solid rgba(224, 148, 31, 0.72);
  border-radius: 14px;
  color: #83540d;
  background: #fff6df;
  font-size: 1rem;
  line-height: 1.65;
}

.confirm-dialog-message + :deep(*) {
  margin-top: 0;
}

.secondary-button,
.primary-button,
.danger-button {
  min-height: 42px;
  padding: 0.55rem 1.25rem;
  border-radius: 12px;
  font: inherit;
  cursor: pointer;
}

.secondary-button {
  border: 1px solid var(--line);
  color: var(--text);
  background: var(--surface-strong);
}

.primary-button,
.danger-button {
  border: 1px solid transparent;
  color: #fff;
  font-weight: 700;
}

.primary-button {
  background: var(--accent);
}

.danger-button {
  background: #e35d6a;
}

.secondary-button:disabled,
.primary-button:disabled,
.danger-button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}
</style>
