<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue"

import NoticeBridge from "@/mobile/components/feedback/NoticeBridge.vue"
import BaseDialog from "@/mobile/components/overlay/BaseDialog.vue"
import { getErrorMessage } from "@/shared/api/errors"
import {
  createDailyTask,
  updateDailyTask,
} from "@/mobile/features/weekly-report/api"
import type {
  DailyWorkTask,
  WeeklyReport,
} from "@/mobile/features/weekly-report/types"

const props = withDefaults(
  defineProps<{
    open: boolean
    report: Pick<WeeklyReport, "id" | "period_start" | "period_end"> | null
    task?: DailyWorkTask | null
    existingTasks?: DailyWorkTask[]
    deferSave?: boolean
  }>(),
  { task: null, existingTasks: () => [], deferSave: false },
)

const emit = defineEmits<{
  close: []
  saved: [task: DailyWorkTask]
}>()

const workDate = ref("")
const workContent = ref("")
const busy = ref(false)
const warningMessage = ref("")

const dateOptions = computed(() => {
  if (!props.report) return []
  const start = toDateInput(props.report.period_start)
  const end = toDateInput(props.report.period_end)
  if (!start || !end || start > end) return []
  const usedDates = new Set(
    props.existingTasks
      .filter((item) => item.id !== props.task?.id)
      .map((item) => toDateInput(item.work_date)),
  )
  const dates: string[] = []
  let cursor = start
  while (cursor <= end) {
    if (!usedDates.has(cursor) || cursor === toDateInput(props.task?.work_date || "")) {
      dates.push(cursor)
    }
    cursor = addDays(cursor, 1)
  }
  return dates
})

const isEditing = computed(() => Boolean(props.task?.id))
const hasAvailableDate = computed(() => dateOptions.value.length > 0)

watch(
  () => [props.open, props.task, props.report, props.existingTasks] as const,
  () => {
    if (!props.open) return
    warningMessage.value = ""
    workContent.value = props.task?.work_content || ""
    if (props.task?.work_date) {
      workDate.value = toDateInput(props.task.work_date)
      return
    }
    const today = localDateInput()
    workDate.value = dateOptions.value.includes(today)
      ? today
      : dateOptions.value[0] || ""
  },
  { immediate: true },
)

function showWarning(message: string) {
  warningMessage.value = ""
  void nextTick(() => {
    warningMessage.value = message
  })
}

async function save() {
  if (!props.report) return
  const content = workContent.value.trim()
  if (!workDate.value) {
    showWarning("请选择日报日期。")
    return
  }
  if (!content) {
    showWarning("主要工作内容不能为空。")
    return
  }
  busy.value = true
  try {
    const payload = { work_date: workDate.value, work_content: content }
    if (props.deferSave || !props.report.id) {
      const now = new Date().toISOString()
      emit("saved", {
        id: props.task?.id || `draft-${Date.now()}-${Math.random().toString(36).slice(2)}`,
        report_id: props.task?.report_id || props.report.id || "",
        work_date: workDate.value,
        work_content: content,
        created_at: props.task?.created_at || now,
        updated_at: now,
      })
      emit("close")
      return
    }
    const saved = isEditing.value
      ? await updateDailyTask(props.task!.report_id || props.report.id, props.task!.id, payload)
      : await createDailyTask(props.report.id, payload)
    emit("saved", saved)
    emit("close")
  } catch (error) {
    showWarning(getErrorMessage(error))
  } finally {
    busy.value = false
  }
}

function toDateInput(value: string) {
  return String(value || "").slice(0, 10)
}

function addDays(value: string, days: number) {
  const current = new Date(`${value}T00:00:00Z`)
  current.setUTCDate(current.getUTCDate() + days)
  return current.toISOString().slice(0, 10)
}

function localDateInput() {
  const today = new Date()
  const year = today.getFullYear()
  const month = String(today.getMonth() + 1).padStart(2, "0")
  const day = String(today.getDate()).padStart(2, "0")
  return `${year}-${month}-${day}`
}

</script>

<template>
  <NoticeBridge :warning-message="warningMessage" />
  <BaseDialog
    :open="open"
    :title="isEditing ? '编辑日报' : '填写日报'"
    width="720px"
    height="520px"
    :busy="busy"
    @close="emit('close')"
  >
    <form class="daily-task-dialog" @submit.prevent="save">
      <label class="daily-task-dialog__field">
        <span class="daily-task-dialog__label">日期<span class="required-mark">*</span></span>
        <select v-model="workDate" :disabled="!hasAvailableDate">
          <option v-for="date in dateOptions" :key="date" :value="date">
            {{ date }}
          </option>
        </select>
      </label>
      <label class="daily-task-dialog__field daily-task-dialog__field--wide">
        <span class="daily-task-dialog__label">
          主要工作内容<span class="required-mark">*</span>
        </span>
        <textarea class="user-content"
          v-model="workContent"
          rows="7"
          maxlength="2000"
          placeholder="请输入主要工作内容"
        />
      </label>
      <p v-if="!hasAvailableDate" class="daily-task-dialog__empty">
        本周没有可填写的日报日期。
      </p>
    </form>
    <template #actions>
      <button class="secondary-button" type="button" :disabled="busy" @click="emit('close')">
        取消
      </button>
      <button
        class="primary-button"
        type="button"
        :disabled="busy || !hasAvailableDate"
        @click="save"
      >
        确认
      </button>
    </template>
  </BaseDialog>
</template>

<style scoped src="./DailyTaskDialog.css"></style>


