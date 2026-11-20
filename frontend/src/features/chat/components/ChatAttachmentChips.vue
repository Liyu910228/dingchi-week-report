<script setup lang="ts">
import { FileText, Image } from "lucide-vue-next"

import { formatAttachmentSize } from "@/features/chat/attachments"
import type { ChatAttachment } from "@/features/chat/types"

withDefaults(
  defineProps<{
    attachments?: ChatAttachment[]
  }>(),
  { attachments: () => [] },
)
</script>

<template>
  <div v-if="attachments.length" class="attachment-chips" aria-label="消息附件">
    <span
      v-for="attachment in attachments"
      :key="attachment.id"
      class="attachment-chip"
      :title="attachment.name"
    >
      <Image v-if="attachment.kind === 'image'" :size="16" aria-hidden="true" />
      <FileText v-else :size="16" aria-hidden="true" />
      <span class="attachment-name">{{ attachment.name }}</span>
      <small>{{ formatAttachmentSize(attachment.size) }}</small>
    </span>
  </div>
</template>

<style scoped src="./ChatAttachmentChips.css"></style>
