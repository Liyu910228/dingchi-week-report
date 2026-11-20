<script setup lang="ts">
import { ref } from "vue"

import {
  MONTHLY_PLAN_ATTACHMENT_PROMPT,
  WEEKLY_REPORT_ATTACHMENT_PROMPT,
} from "@/features/chat/attachments"
import ChatAttachmentPicker from "@/features/chat/components/ChatAttachmentPicker.vue"

const prompt = defineModel<string>({ required: true })

defineProps<{
  isSending: boolean
}>()

const emit = defineEmits<{
  submit: [files: File[]]
}>()

const selectedFiles = ref<File[]>([])

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
  <form class="composer" @submit.prevent="handleSubmit">
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

    <ChatAttachmentPicker v-model="selectedFiles" :disabled="isSending" />

    <div class="composer-input">
      <textarea
        v-model="prompt"
        rows="3"
        maxlength="20000"
        placeholder="输入消息，或添加图片和文档；Enter 发送，Shift + Enter 换行"
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
  </form>
</template>

<style scoped src="./ChatComposer.css"></style>
