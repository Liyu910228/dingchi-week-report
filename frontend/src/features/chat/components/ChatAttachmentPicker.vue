<script setup lang="ts">
import { FileText } from "lucide-vue-next"
import { onBeforeUnmount, ref, watch } from "vue"

import {
  CHAT_ATTACHMENT_ACCEPT,
  formatAttachmentSize,
  isImageChatAttachment,
  isSupportedChatAttachment,
  MAX_CHAT_ATTACHMENT_SIZE,
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

function fileFingerprint(file: File) {
  return `${file.name}:${file.size}:${file.lastModified}`
}

function addFiles(candidates: File[]) {
  selectionError.value = ""
  if (props.disabled || !candidates.length) return
  const existing = new Set(files.value.map(fileFingerprint))
  const incoming = new Set<string>()
  const unique = candidates.filter((file) => {
    const key = fileFingerprint(file)
    if (existing.has(key) || incoming.has(key)) return false
    incoming.add(key)
    return true
  })
  const messages: string[] = []
  if (unique.length !== candidates.length) messages.push("重复文件已跳过")

  const supported = unique.filter((file) => {
    if (!isSupportedChatAttachment(file)) return false
    return file.size > 0 && file.size <= MAX_CHAT_ATTACHMENT_SIZE
  })
  if (supported.length !== unique.length) {
    messages.push("不支持的类型、空文件或超过 10MB 的文件已跳过")
  }

  const remaining = Math.max(0, MAX_CHAT_ATTACHMENTS - files.value.length)
  const accepted = supported.slice(0, remaining)
  if (supported.length > remaining) messages.push("最多只能保留 4 个附件")
  if (accepted.length) files.value = [...files.value, ...accepted]
  if (messages.length) selectionError.value = `${messages.join("；")}。`
  if (!accepted.length && !messages.length) selectionError.value = "没有可添加的附件。"
}

defineExpose({ addFiles })

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
      <small>最多 4 个文件，单个不超过 10MB，支持图片、PDF、Word、Excel 和文本文件</small>
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
