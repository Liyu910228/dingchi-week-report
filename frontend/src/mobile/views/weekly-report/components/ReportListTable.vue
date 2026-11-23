<script setup lang="ts">
import { vRowBackgrounds } from "@/mobile/shared/table/row-backgrounds"
import { vResizableColumns } from "@/mobile/shared/table/resizable-columns"
import { useUserTableResizeKey } from "@/mobile/features/auth/useUserTableResizeKey"
import { computed, ref } from "vue"
import { useAuthStore } from "@/features/auth/store"
import { reopenReport } from "@/mobile/features/weekly-report/api"
import { getErrorMessage } from "@/shared/api/errors"
import ConfirmDialog from "@/mobile/components/feedback/ConfirmDialog.vue"
import NoticeBridge from "@/mobile/components/feedback/NoticeBridge.vue"
import { RouterLink, type LocationQueryRaw } from "vue-router"

import { getReportRoleName } from "@/mobile/features/weekly-report/constants"
import type { WeeklyReport } from "@/mobile/features/weekly-report/types"
import { formatDateTime, formatPeriod } from "@/utils/date"

import ReportStatusTag from "./ReportStatusTag.vue"

type ReportTableScope = "self" | "team" | "all"

const props = withDefaults(
  defineProps<{
    reports: WeeklyReport[]
    scope: ReportTableScope
    isLoading?: boolean
    emptyMessage?: string
    canEdit?: (report: WeeklyReport) => boolean
    canSubmit?: (report: WeeklyReport) => boolean
    canDelete?: (report: WeeklyReport) => boolean
    canCopy?: (report: WeeklyReport) => boolean
    copyBusy?: boolean
    canFillDaily?: (report: WeeklyReport) => boolean
    returnQuery?: LocationQueryRaw
  }>(),
  {
    isLoading: false,
    emptyMessage: "暂无周报",
    canEdit: undefined,
    canSubmit: undefined,
    canDelete: undefined,
    canFillDaily: undefined,
  },
)

const emit = defineEmits<{
  restored: []
  copy: [report: WeeklyReport]
  submit: [report: WeeklyReport]
  delete: [report: WeeklyReport]
  dailyTask: [report: WeeklyReport]
}>()

function canEditReport(report: WeeklyReport) {
  return props.canEdit?.(report) ?? false
}

function canDeleteReport(report: WeeklyReport) {
  return props.canDelete?.(report) ?? false
}

function canSubmitReport(report: WeeklyReport) {
  return props.canSubmit?.(report) ?? false
}

function canFillDailyReport(report: WeeklyReport) {
  return props.canFillDaily?.(report) ?? false
}

function hasActions() {
  return props.scope === "self" || isAdmin.value
}

function editRoute(report: WeeklyReport) {
  return {
    name: "mobile-weekly-report-edit",
    params: { reportId: report.id },
    query: props.returnQuery,
  }
}
const auth = useAuthStore()
const isAdmin = computed(()=>auth.roles.some(role=>role.role_code==="system_admin"))
const restoring = ref<WeeklyReport|null>(null)
const restoreBusy = ref(false)
const restoreError = ref("")
function askRestore(report:WeeklyReport) {
  if(!isAdmin.value || report.status!=="completed" || restoreBusy.value)return
  restoreError.value=""
  restoring.value=report
}
async function confirmRestore() {
  if(!restoring.value || restoreBusy.value)return
  restoreBusy.value=true
  try {
    await reopenReport(restoring.value.id)
    restoring.value=null
    emit("restored")
  } catch(error) { restoreError.value=getErrorMessage(error) }
  finally { restoreBusy.value=false }
}
const resizeKey = useUserTableResizeKey(() => `weekly-report:${props.scope}`)
</script>

<template>
  <div class="report-list-table-wrap">
    <NoticeBridge :warning-message="restoreError" />
    <ConfirmDialog :open="Boolean(restoring)" :busy="restoreBusy" title="恢复周报编辑"
      :message="`确认将${restoring?.employee_name || '该用户'} ${formatPeriod(restoring?.period_start || '',restoring?.period_end || '')}的周报恢复为进行中？恢复后，用户可以修改并重新提交。`"
      confirm-label="恢复编辑" @close="!restoreBusy && (restoring=null)" @confirm="confirmRestore" />
    <table v-row-backgrounds v-resizable-columns="resizeKey" class="report-list-table">
      <thead>
        <tr>
          <th data-column-key="period">周报周期</th>
          <th data-column-key="month_key">所属月度</th>
          <th v-if="scope !== 'self'" data-column-key="employee_name">填写人</th>
          <th data-column-key="role_code">职位</th>
          <th v-if="scope !== 'self'" data-column-key="group_name">分组</th>
          <th data-column-key="status">状态</th>
          <th data-column-key="updated_at">更新时间</th>
          <th v-if="hasActions()" class="actions-heading" data-column-key="actions">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="report in reports" :key="report.id">
          <td data-label="周报周期" class="period-cell">
            <RouterLink
              class="period-link"
              :to="{ name: 'mobile-weekly-report-detail', params: { reportId: report.id }, query: returnQuery }"
            >
              <strong>{{ formatPeriod(report.period_start, report.period_end) }}</strong>
            </RouterLink>
          </td>
          <td data-label="所属月度" class="date-cell">{{ report.month_key }}</td>
          <td data-label="填写人" v-if="scope !== 'self'">{{ report.employee_name || "—" }}</td>
          <td data-label="职位">{{ getReportRoleName(report.role_code, report.role_name) }}</td>
          <td data-label="分组" v-if="scope !== 'self'">{{ report.group_name || "—" }}</td>
          <td data-label="状态"><ReportStatusTag :status="report.status" /></td>
          <td data-label="更新时间" class="date-cell">{{ formatDateTime(report.updated_at) }}</td>
          <td data-label="" v-if="hasActions()" class="action-cell">
            <button v-if="isAdmin && report.status==='completed'" class="table-action" type="button"
              :disabled="restoreBusy" @click="askRestore(report)">恢复编辑</button>
            <button
              v-if="report.status === 'completed' && canCopy?.(report)"
              class="table-action"
              type="button"
              :disabled="copyBusy"
              @click="emit('copy', report)"
            >复制</button>
            <button
              v-if="scope === 'self' && canFillDailyReport(report)"
              class="table-action"
              type="button"
              @click="emit('dailyTask', report)"
            >
              填写日报
            </button>
            <RouterLink
              v-if="canEditReport(report)"
              class="table-action"
              :to="editRoute(report)"
            >
              编辑
            </RouterLink>
            <button
              v-if="canSubmitReport(report)"
              class="table-action table-action--primary"
              type="button"
              @click="emit('submit', report)"
            >
              提交
            </button>
            <button
              v-if="canDeleteReport(report)"
              class="table-action table-action--danger"
              type="button"
              @click="emit('delete', report)"
            >
              删除
            </button>
          </td>
        </tr>
        <tr v-if="isLoading">
          <td :colspan="(scope === 'self' ? 5 : 7) + Number(hasActions())" class="empty-row">正在加载周报数据</td>
        </tr>
        <tr v-else-if="!reports.length">
          <td :colspan="(scope === 'self' ? 5 : 7) + Number(hasActions())" class="empty-row">{{ emptyMessage }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped src="./ReportListTable.css"></style>

