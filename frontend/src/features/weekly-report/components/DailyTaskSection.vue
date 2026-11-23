<script setup lang="ts">
import { vRowBackgrounds } from "@/shared/table/row-backgrounds"
import { computed, ref, watch } from "vue"
import { vResizableColumns } from "@/shared/table/resizable-columns"
import { useTaskTableResizeKey } from "@/features/weekly-report/useTaskTableResizeKey"

import NoticeBridge from "@/components/feedback/NoticeBridge.vue"
import BaseDialog from "@/components/overlay/BaseDialog.vue"
import { deleteDailyTask } from "@/features/weekly-report/api"
import { getErrorMessage } from "@/shared/api/errors"
import { formatDateTime } from "@/utils/date"
import type { DailyWorkTask, WeeklyReport } from "@/features/weekly-report/types"

import DailyTaskDialog from "./DailyTaskDialog.vue"

const props = withDefaults(
  defineProps<{
    report: Pick<WeeklyReport, "id" | "period_start" | "period_end">
    dailyTasks?: DailyWorkTask[]
    canEdit?: boolean
    deferSave?: boolean
  }>(),
  { dailyTasks: () => [], canEdit: false, deferSave: false },
)

const emit = defineEmits<{
  "update:dailyTasks": [value: DailyWorkTask[]]
}>()

const resizeKey = useTaskTableResizeKey("daily", () => undefined)
const items = ref<DailyWorkTask[]>([])
const dialogOpen = ref(false)
const editingTask = ref<DailyWorkTask | null>(null)
const warningMessage = ref("")
const confirmOpen = ref(false)
const pendingDelete = ref<DailyWorkTask | null>(null)
const deleteBusy = ref(false)
const canManage = computed(() => props.canEdit && (props.deferSave || Boolean(props.report?.id)))

watch(
  () => props.dailyTasks,
  (value) => {
    items.value = [...(value || [])].sort((left, right) =>
      left.work_date.localeCompare(right.work_date),
    )
  },
  { immediate: true, deep: true },
)

const emptyColspan = computed(() => (canManage.value ? 5 : 4))

function openCreate() {
  if (!canManage.value) return
  editingTask.value = null
  dialogOpen.value = true
}

function openEdit(task: DailyWorkTask) {
  editingTask.value = task
  dialogOpen.value = true
}

function onSaved(task: DailyWorkTask) {
  const index = items.value.findIndex((item) => item.id === task.id)
  const next = [...items.value]
  if (index === -1) next.push(task)
  else next.splice(index, 1, task)
  items.value = next.sort(sortByDate)
  emit("update:dailyTasks", [...items.value])
}

function removeTask(task: DailyWorkTask) {
  pendingDelete.value = task
  confirmOpen.value = true
}

async function confirmDelete() {
  if (!pendingDelete.value) return
  deleteBusy.value = true
  try {
    if (!props.deferSave) {
      await deleteDailyTask(pendingDelete.value.report_id || props.report.id, pendingDelete.value.id)
    }
    items.value = items.value.filter((item) => item.id !== pendingDelete.value?.id)
    emit("update:dailyTasks", [...items.value])
    confirmOpen.value = false
    pendingDelete.value = null
  } catch (error) {
    warningMessage.value = getErrorMessage(error)
  } finally {
    deleteBusy.value = false
  }
}

function sortByDate(left: DailyWorkTask, right: DailyWorkTask) {
  return left.work_date.localeCompare(right.work_date)
}

function clearWarning() {
  warningMessage.value = ""
}

function displayDate(value: string) {
  return value.slice(0, 10)
}
</script>

<template>
  <section class="dashboard-card detail-card daily-task-card">
    <NoticeBridge :warning-message="warningMessage" />
    <div class="section-heading daily-task-card__heading">
      <h2>每日工作总结</h2>
      <button v-if="canManage" class="primary-button" type="button" @click="openCreate">
        填写日报
      </button>
    </div>
    <div class="daily-task-card__table-wrap">
      <table v-row-backgrounds v-resizable-columns="resizeKey" data-resize-fit="true" class="daily-task-card__table">
        <thead>
          <tr>
            <th data-column-key="serial" class="daily-task-card__serial">序号</th>
            <th data-column-key="work_date" class="daily-task-card__date">日期</th>
            <th data-column-key="work_content">主要工作内容</th>
            <th data-column-key="updated_at" class="daily-task-card__updated">更新日期</th>
            <th v-if="canManage" data-column-key="actions" class="daily-task-card__actions">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(task, index) in items" :key="task.id">
            <td class="daily-task-card__serial">{{ index + 1 }}</td>
            <td class="daily-task-card__date">{{ displayDate(task.work_date) }}</td>
            <td class="daily-task-card__content user-content" :title="task.work_content">
              {{ task.work_content }}
            </td>
            <td class="daily-task-card__updated">{{ formatDateTime(task.updated_at) }}</td>
            <td v-if="canManage" class="daily-task-card__actions">
              <button class="table-action" type="button" @click="openEdit(task)">编辑</button>
              <button class="table-action table-action--danger" type="button" @click="removeTask(task)">
                删除
              </button>
            </td>
          </tr>
          <tr v-if="!items.length">
            <td :colspan="emptyColspan" class="daily-task-card__empty">暂无日报</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>

  <DailyTaskDialog
    :open="dialogOpen"
    :report="report"
    :task="editingTask"
    :existing-tasks="items"
    :defer-save="deferSave"
    @close="dialogOpen = false; clearWarning()"
    @saved="onSaved"
  />

  <BaseDialog
    :open="confirmOpen"
    title="删除日报"
    width="420px"
    :busy="deleteBusy"
    @close="confirmOpen = false"
  >
    <p class="daily-task-card__confirm-text">确认删除这条日报？删除后不可恢复。</p>
    <template #actions>
      <button class="secondary-button" type="button" :disabled="deleteBusy" @click="confirmOpen = false">
        取消
      </button>
      <button class="primary-button daily-task-card__confirm-button" type="button" :disabled="deleteBusy" @click="confirmDelete">
        确认删除
      </button>
    </template>
  </BaseDialog>
</template>

<style scoped src="./DailyTaskSection.css"></style>

