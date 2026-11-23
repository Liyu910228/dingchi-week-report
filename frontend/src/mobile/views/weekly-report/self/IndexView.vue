<script setup lang="ts">
import AlertDialog from "@/mobile/components/feedback/AlertDialog.vue"
import ConfirmDialog from "@/mobile/components/feedback/ConfirmDialog.vue"
import NoticeBridge from "@/mobile/components/feedback/NoticeBridge.vue"
import ReportFilterBar from "../components/ReportFilterBar.vue"
import ReportListTable from "../components/ReportListTable.vue"
import ScrollLoadMore from "@/mobile/components/navigation/ScrollLoadMore.vue"
import DailyTaskDialog from "@/mobile/features/weekly-report/components/DailyTaskDialog.vue"
import { useOwnReportList } from "@/mobile/features/weekly-report/composables/useOwnReportList"
import { TEMPLATE_UNAVAILABLE_MESSAGE } from "@/mobile/features/weekly-report/template-support"

const {
  reports, isLoading, errorMessage,
  page, pageSize, total,
  totalPages, filters, openCreateReport,
  resetFilters, search, canEdit,
  canSubmit, canDelete, canFillDaily,
  authStore, copyBusy, reportCopy,
  copyMessage, copyTitle, removeReport,
  submitOwnReport, openDailyDialog, changePage,
  dailyDialogOpen, dailyDialogReport, dailyDialogTasks,
  closeDailyDialog, onDailySaved, confirmDialogOpen,
  confirmDialogBusy, confirmDialogAction, closeConfirmDialog,
  confirmReportAction, templateWarningOpen,
} = useOwnReportList()
</script>

<template>
  <div class="weekly-report-page">
    <NoticeBridge :warning-message="errorMessage" />

    <section class="dashboard-card report-list-card">
      <Teleport defer to="#weekly-list-create-action"><button class="primary-button" type="button" @click="openCreateReport">填写周报</button>
      </Teleport>
      <ReportFilterBar
        v-model:role-code="filters.role_code"
        v-model:month-key="filters.month_key"
        v-model:period-start="filters.period_start"
        v-model:period-end="filters.period_end"
        @reset="resetFilters"
        @search="search"
      />
      <ReportListTable
        @restored="changePage(page)"
        :reports="reports"
        scope="self"
        :is-loading="isLoading"
        :can-copy="report => report.employee_id === authStore.user?.id"
        :copy-busy="copyBusy"
        @copy="reportCopy.copy"
        :can-edit="canEdit"
        :can-submit="canSubmit"
        :can-delete="canDelete"
        :can-fill-daily="canFillDaily"
        empty-message="暂无个人周报"
        @delete="removeReport"
        @submit="submitOwnReport"
        @daily-task="openDailyDialog"
      />
      <ScrollLoadMore :error="errorMessage"
        :page="page"
        :page-size="pageSize"
        :total="total"
        :total-pages="totalPages"
        :disabled="isLoading"
        @change="changePage"
      />
    </section>
    <AlertDialog
      :open="Boolean(copyMessage)"
      :title="copyTitle"
      :message="copyMessage"
      @close="copyMessage = ''"
    />
    <DailyTaskDialog
      :open="dailyDialogOpen"
      :report="dailyDialogReport"
      :existing-tasks="dailyDialogTasks"
      @close="closeDailyDialog"
      @saved="onDailySaved"
    />
    <ConfirmDialog
      :open="confirmDialogOpen"
      :busy="confirmDialogBusy"
      :title="confirmDialogAction === 'delete' ? '确认删除周报' : '确认提交周报'"
      :message="confirmDialogAction === 'delete'
        ? '删除后周报及其任务、日报和附件将无法恢复，请确认。'
        : '提交后，周报内容将无法修改，请确认已完成本周期周报内容的录入。'"
      :confirm-label="confirmDialogAction === 'delete' ? '确认删除' : '确认提交'"
      :confirm-variant="confirmDialogAction === 'delete' ? 'danger' : 'primary'"
      @close="closeConfirmDialog"
      @confirm="confirmReportAction"
    />
    <AlertDialog
      :open="templateWarningOpen"
      title="无法填写周报"
      :message="TEMPLATE_UNAVAILABLE_MESSAGE"
      @close="templateWarningOpen = false"
    />
  </div>
</template>

<style scoped src="./IndexView.css"></style>
