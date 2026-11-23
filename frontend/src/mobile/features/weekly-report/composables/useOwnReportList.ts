import { computed, onMounted, reactive, ref, watch } from "vue"
import { useRouter } from "vue-router"

import { useAuthStore } from "@/features/auth/store"
import { deleteReport, submitReport } from "@/mobile/features/weekly-report/api"
import { useReportDailyEntry } from "./useReportDailyEntry"
import { useReportCopy } from "@/mobile/features/weekly-report/composables/useReportCopy"
import { useReportList } from "@/mobile/features/weekly-report/composables/useReportList"
import type { ReportListFilters, WeeklyReport } from "@/mobile/features/weekly-report/types"


export function useOwnReportList() {
  const authStore = useAuthStore()
  const router = useRouter()
  const reportList = useReportList()
  const filters = reactive({
    role_code: "",
    month_key: "",
    period_start: "",
    period_end: "",
  })
  const reports = computed(() => reportList.reports.value)
  const isLoading = computed(() => reportList.isLoading.value)
  const errorMessage = computed(() => reportList.errorMessage.value)
  const page = computed(() => reportList.page.value)
  const pageSize = computed(() => reportList.pageSize.value)
  const total = computed(() => reportList.total.value)
  const totalPages = computed(() => reportList.totalPages.value)
  // 周报页面由当前角色绑定的 report_template_code 在路由目标内部解析，
  // 列表页不再按角色编码硬编码分流。
  const createRouteName = computed(() => "mobile-weekly-report-new")
  const daily = useReportDailyEntry(message => { reportList.errorMessage.value = message })
  const { open: dailyDialogOpen, report: dailyDialogReport, tasks: dailyDialogTasks,
    show: openDailyDialog, close: closeDailyDialog, saved: onDailySaved } = daily
  const confirmDialogOpen = ref(false)
  const confirmDialogBusy = ref(false)
  const confirmDialogAction = ref<"delete" | "submit">("submit")
  const confirmDialogReport = ref<WeeklyReport | null>(null)
  const templateWarningOpen = ref(false)
  const reportCopy = useReportCopy(loadReports)
  const { busy: copyBusy, message: copyMessage, title: copyTitle } = reportCopy

  function openCreateReport() {
    void router.push({ name: createRouteName.value })
  }

  function queryFilters(): ReportListFilters {
    return {
      role_code: filters.role_code || undefined,
      month_key: filters.month_key || undefined,
      period_start: filters.period_start || undefined,
      period_end: filters.period_end || undefined,
    }
  }

  async function loadReports() {
    if (!authStore.isAuthenticated) return
    await reportList.load(queryFilters())
  }

  function search() {
    reportList.resetPage()
    void loadReports()
  }

  function resetFilters() {
    filters.role_code = ""
    filters.month_key = ""
    filters.period_start = ""
    filters.period_end = ""
    search()
  }

  function canEdit(report: WeeklyReport) {
    return report.status !== "completed" && report.employee_id === authStore.user?.id
  }

  function canDelete(report: WeeklyReport) {
    return canEdit(report)
  }

  function canSubmit(report: WeeklyReport) {
    return report.status === "in_progress" && report.employee_id === authStore.user?.id
  }

  function canFillDaily(report: WeeklyReport) {
    return canSubmit(report)
  }

  async function removeReport(report: WeeklyReport) {
    confirmDialogAction.value = "delete"
    confirmDialogReport.value = report
    confirmDialogOpen.value = true
  }

  async function submitOwnReport(report: WeeklyReport) {
    confirmDialogAction.value = "submit"
    confirmDialogReport.value = report
    confirmDialogOpen.value = true
  }

  function closeConfirmDialog() {
    if (confirmDialogBusy.value) return
    confirmDialogOpen.value = false
    confirmDialogReport.value = null
  }

  async function confirmReportAction() {
    const report = confirmDialogReport.value
    if (!report) return
    confirmDialogBusy.value = true
    try {
      if (confirmDialogAction.value === "delete") await deleteReport(report.id)
      else await submitReport(report.id)
      confirmDialogBusy.value = false
      closeConfirmDialog()
      reportList.resetPage()
      await loadReports()
    } catch (error) {
      reportList.errorMessage.value = error instanceof Error
        ? error.message
        : confirmDialogAction.value === "delete" ? "删除周报失败。" : "提交周报失败。"
    } finally {
      confirmDialogBusy.value = false
    }
  }

  function changePage(page: number) {
    reportList.setPage(page)
    void loadReports()
  }

  onMounted(() => void loadReports())
  watch(() => authStore.effectiveRole?.role_code, () => {
    reportList.resetPage()
    void loadReports()
  })
  return {
    reports,
    isLoading,
    errorMessage,
    page,
    pageSize,
    total,
    totalPages,
    filters,
    openCreateReport,
    resetFilters,
    search,
    canEdit,
    canSubmit,
    canDelete,
    canFillDaily,
    authStore,
    copyBusy,
    reportCopy,
    copyMessage,
    copyTitle,
    removeReport,
    submitOwnReport,
    openDailyDialog,
    changePage,
    dailyDialogOpen,
    dailyDialogReport,
    dailyDialogTasks,
    closeDailyDialog,
    onDailySaved,
    confirmDialogOpen,
    confirmDialogBusy,
    confirmDialogAction,
    closeConfirmDialog,
    confirmReportAction,
    templateWarningOpen,
  }
}

