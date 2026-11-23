<script setup lang="ts">
import { computed } from "vue"

import BaseDialog from "@/components/overlay/BaseDialog.vue"
import AttachmentDownloadLink from "@/components/file/AttachmentDownloadLink.vue"
import {
  allReportTaskFields,
  formatReportTaskField,
  reportTaskUpdatedAt,
} from "@/features/weekly-report/task-fields"
import type {
  ReportAttachment,
  ReportItem,
  ReportTemplateField,
} from "@/features/weekly-report/types"

const props = defineProps<{
  open: boolean
  item: ReportItem | null
  fields?: ReportTemplateField[] | null
  attachments?: ReportAttachment[]
}>()

const emit = defineEmits<{ close: [] }>()

const wideFields = new Set([
  "work_content",
  "output_description",
  "progress_text",
  "delay_reason",
  "document_links",
])

const hasPrimaryField = computed(() => {
  const configuredFields = props.fields || []
  if (configuredFields.length) {
    return configuredFields.some((field) =>
      field.field_code === "customer_name" || field.field_code === "dimension",
    )
  }

  const item = props.item
  if (!item) return true
  if (item.customer_name_snapshot) return true
  return /recruitment|recruit|招聘/i.test(
    `${item.section_code || ""} ${item.section_name_snapshot || ""}`,
  )
})

// 查看页沿用填写页的字段分组顺序：首行主字段/工作任务，长文本独占一行，
// 日期、进度、责任分工分别按填写表单的行顺序展示，避免详情页按字典顺序重新排版。
const fields = computed(() => {
  const source = new Map(
    allReportTaskFields(props.fields).map((field) => [field.field_code, field]),
  )
  const editorOrder = [
    "customer_name",
    "dimension",
    "task_name",
    "work_content",
    "output_description",
    "planned_completion_date",
    "actual_completion_date",
    "progress_text",
    "progress_percent",
    "quality_percent",
    "completion_rate",
    "delay_reason",
    "owner_name",
    "collaborator_names",
    "document_links",
  ]
  return editorOrder
    .map((fieldCode) => source.get(fieldCode))
    .filter((field): field is ReportTemplateField => Boolean(field))
    .filter((field) => {
      if (field.field_code === "on_time_status") return false
      if (!hasPrimaryField.value && (field.field_code === "customer_name" || field.field_code === "dimension")) {
        return false
      }
      return true
    })
})
</script>

<template>
  <BaseDialog :open="open" title="任务详情" width="920px" @close="emit('close')">
    <div v-if="item" class="report-task-detail">
      <div class="report-task-detail__grid">
        <div
          v-for="field in fields"
          :key="field.field_code"
          class="report-task-detail__item"
          :class="{
            'report-task-detail__item--wide':
              wideFields.has(field.field_code)
              || (!hasPrimaryField && field.field_code === 'task_name'),
          }"
        >
          <span class="report-task-detail__label">{{ field.label }}</span>
          <p class="report-task-detail__value" :class="{'user-content':field.field_code!=='on_time_status'}">{{ formatReportTaskField(item, field.field_code) }}</p>
        </div>
        <div class="report-task-detail__item">
          <span class="report-task-detail__label">状态</span>
          <p class="report-task-detail__value">{{ formatReportTaskField(item, "on_time_status") }}</p>
        </div>
        <div class="report-task-detail__item">
          <span class="report-task-detail__label">更新时间</span>
          <p class="report-task-detail__value">{{ reportTaskUpdatedAt(item) }}</p>
        </div>
      </div>

      <div v-if="attachments?.length" class="report-task-detail__attachments">
        <span class="report-task-detail__label">附件</span>
        <ul>
          <li v-for="attachment in attachments" :key="attachment.id">
            <AttachmentDownloadLink
              :attachment-id="attachment.id"
              :file-name="attachment.file_name"
            />
            <small>{{ attachment.description || "已上传" }}</small>
          </li>
        </ul>
      </div>
    </div>
    <template #actions>
      <button class="primary-button" type="button" @click="emit('close')">关闭</button>
    </template>
  </BaseDialog>
</template>

<style scoped src="./ReportTaskDetailDialog.css"></style>
