<script setup lang="ts">
import { ref } from "vue"

import {
  MONTHLY_PLAN_ATTACHMENT_PROMPT,
  WEEKLY_REPORT_ATTACHMENT_PROMPT,
} from "@/features/chat/attachments"
import ChatAttachmentPicker from "@/features/chat/components/ChatAttachmentPicker.vue"
import { useAttachmentDropZone } from "@/features/chat/useAttachmentDropZone"

const prompt = defineModel<string>({ required: true })

const props = defineProps<{
  isSending: boolean
}>()

const emit = defineEmits<{
  submit: [files: File[]]
}>()

const selectedFiles = ref<File[]>([])
const attachmentPicker = ref<InstanceType<typeof ChatAttachmentPicker> | null>(null)
const {
  isDragging,
  handlePaste,
  handleDragEnter,
  handleDragOver,
  handleDragLeave,
  handleDrop,
} = useAttachmentDropZone(
  (files) => attachmentPicker.value?.addFiles(files),
  () => props.isSending,
)

function handleSubmit() {
  if ((!prompt.value.trim() && !selectedFiles.value.length)) return
  const files = [...selectedFiles.value]
  selectedFiles.value = []
  emit("submit", files)
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault()
    handleSubmit()
  }
}
</script>

<template>
  <form
    class="composer"
    :class="{ 'is-dragging': isDragging }"
    @submit.prevent="handleSubmit"
    @paste="handlePaste"
    @dragenter="handleDragEnter"
    @dragover="handleDragOver"
    @dragleave="handleDragLeave"
    @drop="handleDrop"
  >
    <div class="attachment-shortcuts" aria-label="附件快捷提示词">
      <button
        class="ghost-button"
        type="button"
        :disabled="isSending || !selectedFiles.length"
        @click="prompt = WEEKLY_REPORT_ATTACHMENT_PROMPT"
      >
        根据附件写周报
      </button>
      <button
        class="ghost-button"
        type="button"
        :disabled="isSending || !selectedFiles.length"
        @click="prompt = MONTHLY_PLAN_ATTACHMENT_PROMPT"
      >
        根据附件写月度计划
      </button>
    </div>

    <ChatAttachmentPicker ref="attachmentPicker" v-model="selectedFiles" :disabled="isSending" />

    <div class="composer-input">
      <textarea
        v-model="prompt"
        rows="3"
        maxlength="20000"
        placeholder="输入消息，Ctrl+V 粘贴截图/文件，或拖入图片和文档；Enter 发送"
        :disabled="isSending"
        @keydown="handleKeydown"
      />
      <button
        class="primary-button"
        type="submit"
        :disabled="(!prompt.trim() && !selectedFiles.length) || isSending"
      >
        {{ isSending ? "发送中" : "发送" }}
      </button>
    </div>
    <div v-if="isDragging" class="drop-zone-message" role="status">
      松开鼠标，将文件添加到当前消息
    </div>
    <small v-else class="composer-input-hint">支持粘贴或拖入文件，单个不超过 10MB</small>
  </form>
</template>

<style scoped src="./ChatComposer.css"></style>
