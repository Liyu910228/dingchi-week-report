<script setup lang="ts">
import { ref } from "vue"

import NoticeBridge from "@/mobile/components/feedback/NoticeBridge.vue"
import { useChatStore } from "@/mobile/features/chat/store"

import ChatComposer from "./ChatComposer.vue"
import ChatMessageList from "./ChatMessageList.vue"
import ChatToolbar from "./ChatToolbar.vue"

const chatStore = useChatStore()
const prompt = ref("")

async function submit(files: File[]) {
  const content = prompt.value
  if (!content.trim() && !files.length) return

  prompt.value = ""
  await chatStore.send(content, files)
}
</script>

<template>
  <section class="chat-panel surface-card" aria-label="AI 对话">
    <ChatToolbar
      :active-model="chatStore.activeModel"
      :has-messages="chatStore.hasMessages"
      :is-sending="chatStore.isSending"
      @clear="chatStore.clear"
    />

    <ChatMessageList :messages="chatStore.messages" :is-sending="chatStore.isSending" />

    <NoticeBridge :warning-message="chatStore.error" />

    <ChatComposer v-model="prompt" :is-sending="chatStore.isSending" @submit="submit" />
  </section>
</template>

<style scoped src="./ChatPanel.css"></style>
