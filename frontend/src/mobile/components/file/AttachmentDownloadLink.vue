<script setup lang="ts">
import { ref } from "vue"

import { useNoticeStore } from "@/app/stores/notice"
import { downloadReportAttachment } from "@/mobile/features/weekly-report/api"

const props = defineProps<{
  attachmentId?: string
  fileName: string
}>()

const downloading = ref(false)
const noticeStore = useNoticeStore()

async function download(): Promise<void> {
  if (!props.attachmentId || downloading.value) return
  downloading.value = true
  try {
    await downloadReportAttachment(props.attachmentId, props.fileName)
  } catch (error) {
    noticeStore.warning(error instanceof Error ? error.message : "附件下载失败。")
  } finally {
    downloading.value = false
  }
}
</script>

<template>
  <button
    v-if="attachmentId"
    class="attachment-download-link"
    type="button"
    :disabled="downloading"
    @click="download"
  >
    {{ downloading ? "下载中…" : fileName }}
  </button>
  <span v-else>{{ fileName }}</span>
</template>

<style scoped>
.attachment-download-link {
  appearance: none;
  border: 0;
  padding: 0;
  color: #1677e8;
  background: transparent;
  font: inherit;
  cursor: pointer;
}

.attachment-download-link:hover:not(:disabled) {
  text-decoration: underline;
}

.attachment-download-link:disabled {
  cursor: wait;
  opacity: 0.65;
}
</style>
