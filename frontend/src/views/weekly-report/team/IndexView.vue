<script setup lang="ts">
import AlertDialog from "@/components/feedback/AlertDialog.vue"
import ConfirmDialog from "@/components/feedback/ConfirmDialog.vue"
import NoticeBridge from "@/components/feedback/NoticeBridge.vue"
import ReportFilterBar from "../components/ReportFilterBar.vue"
import ReportListTable from "../components/ReportListTable.vue"
import ReportPagination from "@/features/weekly-report/components/ReportPagination.vue"
import DailyTaskDialog from "@/features/weekly-report/components/DailyTaskDialog.vue"
import { useTeamReportList } from "./composables/useTeamReportList"
const {
  activeTab, reports, isLoading, errorMessage, groups,
  filters, returnQuery, page, pageSize, total,
  totalPages, openCreateReport, switchTab, resetFilters, search,
  canEdit, canSubmit, canDelete, removeReport, submitOwnReport,
  changePage, confirmDialogOpen, confirmDialogBusy, confirmDialogAction, closeConfirmDialog,
  confirmReportAction, authStore, reportCopy, copyBusy, copyMessage,
  copyTitle, dailyDialogOpen, dailyDialogReport, dailyDialogTasks, openDailyDialog,
  closeDailyDialog, onDailySaved
} = useTeamReportList()
</script>

<template>
  <div class="weekly-report-page">
    <NoticeBridge :warning-message="errorMessage" />

    <section class="dashboard-card report-list-card">
      <Teleport defer to="#weekly-list-create-action"><button v-if="activeTab === 'self'" class="primary-button" type="button" @click="openCreateReport">填写周报</button>
      </Teleport>
      <ReportFilterBar
        v-model:role-code="filters.role_code"
        v-model:month-key="filters.month_key"
        v-model:period-start="filters.period_start"
        v-model:period-end="filters.period_end"
        v-model:group-id="filters.group_id"
        :group-options="groups"
        show-group
        @reset="resetFilters"
        @search="search"
      />
      <ReportListTable
        @restored="changePage(page)"
        :reports="reports"
        :scope="activeTab === 'self' ? 'self' : 'team'"
        :return-query="returnQuery"
        :is-loading="isLoading"
        :can-edit="canEdit"
        :can-submit="canSubmit"
        :can-delete="canDelete"
        :can-copy="report => activeTab === 'self' && report.employee_id === authStore.user?.id"
        :copy-busy="copyBusy"
        :can-fill-daily="canSubmit"
        @copy="reportCopy.copy"
        @daily-task="openDailyDialog"
        :empty-message="activeTab === 'self' ? '暂无个人周报' : '暂无团队成员周报'"
        @delete="removeReport"
        @submit="submitOwnReport"
      />
      <ReportPagination
        :page="page"
        :page-size="pageSize"
        :total="total"
        :total-pages="totalPages"
        :disabled="isLoading"
        @change="changePage"
      />
    </section>
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
    <AlertDialog :open="Boolean(copyMessage)" :title="copyTitle" :message="copyMessage" @close="copyMessage = ''" />
    <DailyTaskDialog :open="dailyDialogOpen" :report="dailyDialogReport" :existing-tasks="dailyDialogTasks" @close="closeDailyDialog" @saved="onDailySaved" />
  </div>
</template>

<style scoped src="./IndexView.css"></style>


