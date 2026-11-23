<script setup lang="ts">
withDefaults(
  defineProps<{
    open: boolean
    title: string
    message: string
    isDeleting?: boolean
  }>(),
  { isDeleting: false },
)

const emit = defineEmits<{
  close: []
  confirm: []
}>()
</script>

<template>
  <div v-if="open" class="confirm-layer">
    <div class="confirm-backdrop">
      <section class="confirm-panel" role="alertdialog" aria-modal="true" :aria-label="title">
        <h2>{{ title }}</h2>
        <p>{{ message }}</p>
        <div class="confirm-actions">
          <button class="secondary-button" type="button" :disabled="isDeleting" @click="emit('close')">取消</button>
          <button class="danger-button" type="button" :disabled="isDeleting" @click="emit('confirm')">
            {{ isDeleting ? "删除中…" : "确认删除" }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped src="./ConfirmDeleteDialog.css"></style>
