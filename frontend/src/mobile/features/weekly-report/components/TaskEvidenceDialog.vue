<script setup lang="ts">
import { ref, watch } from "vue"
import BaseDialog from "@/mobile/components/overlay/BaseDialog.vue"
import AttachmentDownloadLink from "@/mobile/components/file/AttachmentDownloadLink.vue"
import { uploadPendingReportAttachment } from "@/mobile/features/weekly-report/api"
import type { TaskAttachment } from "@/mobile/features/weekly-report/task-draft"

const props = defineProps<{ open: boolean; links: string; attachments: TaskAttachment[]; readonly?:boolean }>()
const emit = defineEmits<{ close: []; save: [links: string, attachments: TaskAttachment[]] }>()
const links = ref("")
const attachments = ref<TaskAttachment[]>([])
const busy = ref(false)
const error = ref("")
const fileInput = ref<HTMLInputElement | null>(null)
watch(() => [props.open, props.links, props.attachments], () => {
  if (!props.open) return
  links.value = props.links
  attachments.value = props.attachments.map(item => ({ ...item }))
  error.value = ""
}, { immediate: true })

async function upload(event: Event) {
  const input = event.target as HTMLInputElement
  const files = [...(input.files || [])]
  input.value = ""
  if (props.readonly || busy.value || !files.length) return
  busy.value = true
  error.value = ""
  try {
    for (const file of files) {
      if (attachments.value.some(item => item.file_name === file.name && item.file_size === file.size)) continue
      const attachment = await uploadPendingReportAttachment(file)
      attachments.value.push({ ...attachment })
    }
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : "附件上传失败，请重试。"
  } finally {
    busy.value = false
  }
}
function save() {
  if (props.readonly || busy.value) return
  emit("save", links.value.trim(), attachments.value.map(item => ({ ...item })))
}
</script>

<template>
  <BaseDialog :open="open" :title="readonly ? '查看相关文档链接或佐证材料' : '编辑相关文档链接或佐证材料'" width="860px" height="80vh" :busy="busy" @close="emit('close')">
    <form id="task-evidence-form" class="evidence-form" @submit.prevent="save">
      <label class="evidence-label">相关文档链接或佐证材料<textarea class="user-content" :readonly="readonly" v-model="links" rows="6" :disabled="busy" placeholder="填写文档链接或材料说明" /></label>
      <div class="attachment-heading"><strong>附件（{{ attachments.length }}）</strong><button v-if="!readonly" class="ghost-button" type="button" :disabled="busy" @click="fileInput?.click()">{{ busy ? '上传中…' : attachments.length ? '继续上传附件' : '上传附件' }}</button><input ref="fileInput" class="file-input" type="file" multiple :disabled="busy || readonly" aria-label="选择附件" @change="upload" /></div>
      <p v-if="error" class="evidence-error" role="alert">{{ error }}</p>
      <p v-if="!attachments.length" class="empty-attachments">{{readonly ? '暂无附件。' : '暂无附件，可选择多个文件上传。'}}</p>
      <div v-for="(attachment, index) in attachments" :key="attachment.id || `${attachment.file_name}-${index}`" class="attachment-item">
        <div class="attachment-name"><AttachmentDownloadLink :attachment-id="attachment.id" :file-name="attachment.file_name" /></div>
        <label>附件说明<input class="user-content" :readonly="readonly" v-model="attachment.description" maxlength="500" placeholder="附件说明（可选）" :disabled="busy" /></label>
        <button v-if="!readonly" type="button" class="remove-attachment" :disabled="busy" @click="attachments.splice(index, 1)">移除</button>
      </div>
    </form>
    <template #actions><button class="ghost-button" type="button" :disabled="busy" @click="emit('close')">{{readonly ? '关闭' : '取消'}}</button><button v-if="!readonly" class="primary-button" type="submit" form="task-evidence-form" :disabled="busy">确定</button></template>
  </BaseDialog>
</template>

<style scoped src="./TaskEvidenceDialog.css"></style>
