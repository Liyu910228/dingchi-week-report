<script setup lang="ts">
defineProps<{
  activeModel: string
  hasMessages: boolean
  isSending: boolean
}>()

const emit = defineEmits<{
  clear: []
}>()
</script>

<template>
  <div class="chat-toolbar">
    <div>
      <span class="eyebrow">OPENAI-COMPATIBLE API</span>
      <h2>周报 AI 助手</h2>
    </div>
    <div class="toolbar-actions">
      <span v-if="activeModel" class="model-tag">{{ activeModel }}</span>
      <button
        class="text-button"
        type="button"
        :disabled="!hasMessages || isSending"
        @click="emit('clear')"
      >
        清空对话
      </button>
    </div>
  </div>
</template>

<style scoped src="./ChatToolbar.css"></style>
