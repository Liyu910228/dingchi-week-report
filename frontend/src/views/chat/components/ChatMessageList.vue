<script setup lang="ts">
import { nextTick, useTemplateRef, watch } from "vue"

import ChatAttachmentChips from "@/features/chat/components/ChatAttachmentChips.vue"
import type { ChatEntry } from "@/features/chat/types"

const props = defineProps<{
  messages: ChatEntry[]
  isSending: boolean
}>()

const messageList = useTemplateRef<HTMLDivElement>("messageList")

watch(
  [() => props.messages.length, () => props.isSending],
  async () => {
    await nextTick()
    messageList.value?.scrollTo({ top: messageList.value.scrollHeight, behavior: "smooth" })
  },
)
</script>

<template>
  <div ref="messageList" class="message-list" aria-live="polite">
    <div v-if="!messages.length" class="empty-chat">
      <strong>从一个具体任务开始</strong>
      <p>例如：帮我把本周完成事项整理成管理层周报。</p>
    </div>

    <article
      v-for="message in messages"
      :key="message.id"
      class="message"
      :class="'message-' + message.role"
    >
      <span>{{ message.role === "user" ? "你" : "AI" }}</span>
      <div class="message-body">
        <ChatAttachmentChips :attachments="message.attachments" />
        <p>{{ message.content }}</p>
      </div>
    </article>

    <article v-if="isSending" class="message message-assistant pending-message">
      <span>AI</span>
      <p>正在思考<span class="typing-dots">...</span></p>
    </article>
  </div>
</template>

<style scoped src="./ChatMessageList.css"></style>
