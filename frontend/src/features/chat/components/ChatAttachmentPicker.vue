<script setup lang="ts">
import { FileText } from "lucide-vue-next"
import { onBeforeUnmount, ref, watch } from "vue"

import {
  CHAT_ATTACHMENT_ACCEPT,
  formatAttachmentSize,
  isImageChatAttachment,
  isSupportedChatAttachment,
  MAX_CHAT_ATTACHMENTS,
} from "@/features/chat/attachments"

interface AttachmentPreview {
  id: number
  file: File
  url: string
}

const files = defineModel<File[]>({ required: true })
const props = defineProps<{
  disabled: boolean
}>()

const fileInput = ref<HTMLInputElement | null>(null)
const previews = ref<AttachmentPreview[]>([])
const selectionError = ref("")
let nextPreviewId = 1

function syncPreviews(nextFiles: File[]) {
  for (const preview of previews.value) {
    if (!nextFiles.includes(preview.file) && preview.url) URL.revokeObjectURL(preview.url)
  }
  const retained = previews.value.filter((preview) => nextFiles.includes(preview.file))
  const retainedFiles = new Set(retained.map((preview) => preview.file))
  const added = nextFiles
    .filter((file) => !retainedFiles.has(file))
    .map((file) => ({
      id: nextPreviewId++,
      file,
      url: isImageChatAttachment(file) ? URL.createObjectURL(file) : "",
    }))
  previews.value = nextFiles.map((file) => {
    const existing = [...retained, ...added].find((preview) => preview.file === file)
    return existing as AttachmentPreview
  })
}

watch(files, syncPreviews, { immediate: true })

function addFiles(candidates: File[]) {
  selectionError.value = ""
  const supported = candidates.filter((file) => isSupportedChatAttachment(file))
  if (supported.length !== candidates.length) {
    selectionError.value = "包含不支持的文件类型，请选择图片、PDF、Word、Excel 或文本文件。"
    return
  }
  const remaining = MAX_CHAT_ATTACHMENTS - files.value.length
  if (candidates.length > remaining) selectionError.value = "最多可选择 4 个附件。"
  files.value = [...files.value, ...supported.slice(0, Math.max(0, remaining))]
}

function handleSelection(event: Event) {
  const input = event.target as HTMLInputElement
  addFiles(Array.from(input.files ?? []))
  input.value = ""
}

function removeFile(index: number) {
  selectionError.value = ""
  files.value = files.value.filter((_, fileIndex) => fileIndex !== index)
}

onBeforeUnmount(() => {
  for (const preview of previews.value) {
    if (preview.url) URL.revokeObjectURL(preview.url)
  }
})
</script>

<template>
  <div class="attachment-picker">
    <div class="attachment-picker-heading">
      <button
        class="ghost-button"
        type="button"
        :disabled="props.disabled || files.length >= MAX_CHAT_ATTACHMENTS"
        @click="fileInput?.click()"
      >
        添加附件
      </button>
      <small>最多 4 个文件，支持图片、PDF、Word、Excel 和文本文件</small>
    </div>
    <input
      ref="fileInput"
      class="attachment-input"
      type="file"
      multiple
      :accept="CHAT_ATTACHMENT_ACCEPT"
      :disabled="props.disabled"
      @change="handleSelection"
    />

    <ul v-if="previews.length" class="attachment-preview-list" aria-label="待发送附件">
      <li v-for="(preview, index) in previews" :key="preview.id" class="attachment-preview">
        <img v-if="preview.url" :src="preview.url" :alt="`${preview.file.name} 预览`" />
        <span v-else class="document-preview" aria-hidden="true"><FileText :size="22" /></span>
        <span class="attachment-preview-info">
          <strong :title="preview.file.name">{{ preview.file.name }}</strong>
          <small>{{ formatAttachmentSize(preview.file.size) }}</small>
        </span>
        <button
          class="text-button remove-attachment"
          type="button"
          :disabled="props.disabled"
          :aria-label="`移除附件 ${preview.file.name}`"
          @click="removeFile(index)"
        >
          移除
        </button>
      </li>
    </ul>
    <p v-if="selectionError" class="selection-error" role="alert">{{ selectionError }}</p>
  </div>
</template>

<style scoped src="./ChatAttachmentPicker.css"></style>
