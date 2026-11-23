import { computed, onMounted, reactive, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import type { LocationQueryRaw } from "vue-router"

import { listGroups } from "@/features/directory/api"
import type { DirectoryGroup } from "@/features/directory/types"
import { useAuthStore } from "@/features/auth/store"
import { deleteReport, submitReport } from "@/features/weekly-report/api"
import { useReportList } from "@/features/weekly-report/composables/useReportList"
import type { ReportListFilters, WeeklyReport } from "@/features/weekly-report/types"
import { useReportCopy } from "@/features/weekly-report/composables/useReportCopy"
import { useReportDailyEntry } from "@/features/weekly-report/composables/useReportDailyEntry"

type ReportTab = "self" | "team"

export function useTeamReportList() {
  const authStore = useAuthStore()
  const route = useRoute()
  const router = useRouter()
  const reportList = useReportList()
  const activeTab = ref<ReportTab>("self")
  const groups = ref<DirectoryGroup[]>([])
  const confirmDialogOpen = ref(false)
  const confirmDialogBusy = ref(false)
  const confirmDialogAction = ref<"delete" | "submit">("submit")
  const confirmDialogReport = ref<WeeklyReport | null>(null)
  const reportCopy = useReportCopy(loadReports)
  const { busy: copyBusy, message: copyMessage, title: copyTitle } = reportCopy
  const daily = useReportDailyEntry(message => { reportList.errorMessage.value = message })
  const { open: dailyDialogOpen, report: dailyDialogReport, tasks: dailyDialogTasks,
    show: openDailyDialog, close: closeDailyDialog, saved: onDailySaved } = daily
  const filters = reactive({
    role_code: "",
    month_key: "",
    period_start: "",
    period_end: "",
    group_id: "",
    employee_id: "",
  })
  const reports = computed(() => reportList.reports.value)
  const isLoading = computed(() => reportList.isLoading.value)
  const errorMessage = computed(() => reportList.errorMessage.value)
  const page = computed(() => reportList.page.value)
  const pageSize = computed(() => reportList.pageSize.value)
  const total = computed(() => reportList.total.value)
  const totalPages = computed(() => reportList.totalPages.value)
  const createRouteName = computed(() => "weekly-report-new")
  const returnQuery = computed<LocationQueryRaw>(() => ({
    tab: activeTab.value,
    filter_role_code: filters.role_code || undefined,
    month_key: filters.month_key || undefined,
    period_start: filters.period_start || undefined,
    period_end: filters.period_end || undefined,
    group_id: filters.group_id || undefined,
    employee_id: filters.employee_id || undefined,
    page: String(page.value),
  }))

  function openCreateReport() {
    void router.push({ name: createRouteName.value, query: returnQuery.value })
  }

  function queryFilters(): ReportListFilters {
    return {
      role_code: filters.role_code || undefined,
      month_key: filters.month_key || undefined,
      period_start: filters.period_start || undefined,
      period_end: filters.period_end || undefined,
      group_id: filters.group_id || undefined,
      employee_id: filters.employee_id || undefined,
      employee_scope: activeTab.value,
    }
  }

  function queryValue(value: unknown) {
    return Array.isArray(value) ? String(value[0] || "") : String(value || "")
  }

  function syncRouteFilters() {
    filters.role_code = queryValue(route.query.filter_role_code)
    filters.month_key = queryValue(route.query.month_key)
    filters.period_start = queryValue(route.query.period_start)
    filters.period_end = queryValue(route.query.period_end)
    filters.group_id = queryValue(route.query.group_id)
    filters.employee_id = queryValue(route.query.employee_id)

    const requestedTab = queryValue(route.query.tab)
    const currentEmployeeId = String(authStore.user?.id || "")
    if (requestedTab === "self" || requestedTab === "team") activeTab.value = requestedTab
    else if (filters.employee_id && filters.employee_id === currentEmployeeId) activeTab.value = "self"
    else if (filters.employee_id || filters.group_id) activeTab.value = "team"

    const requestedPage = Number(queryValue(route.query.page))
    if (Number.isInteger(requestedPage) && requestedPage > 0) reportList.setPage(requestedPage)
    else reportList.resetPage()
  }

  function currentListState() {
    return JSON.stringify([
      activeTab.value,
      filters.role_code,
      filters.month_key,
      filters.period_start,
      filters.period_end,
      filters.group_id,
      filters.employee_id,
      page.value,
    ])
  }

  async function loadReports() {
    if (!authStore.isAuthenticated) return
    await reportList.load(queryFilters())
  }

  async function loadGroups() {
    try {
      groups.value = (await listGroups()).items
    } catch (error) {
      reportList.errorMessage.value = error instanceof Error ? error.message : "分组加载失败。"
    }
  }

  function search() {
    reportList.resetPage()
    void router.replace({ query: returnQuery.value })
    void loadReports()
  }

  function resetFilters() {
    filters.role_code = ""
    filters.month_key = ""
    filters.period_start = ""
    filters.period_end = ""
    filters.group_id = ""
    filters.employee_id = ""
    search()
  }

  function switchTab(tab: ReportTab) {
    if (activeTab.value === tab) return
    activeTab.value = tab
    // 清除首页跳转带入的目标人员/分组，避免切换到“我的周报”后仍沿用团队筛选。
    filters.employee_id = ""
    if (tab === "self") filters.group_id = ""
    reportList.resetPage()
    void router.replace({ query: returnQuery.value })
    void loadReports()
  }

  function canEdit(report: WeeklyReport) {
    return activeTab.value === "self" && report.status !== "completed" && report.employee_id === authStore.user?.id
  }

  function canDelete(report: WeeklyReport) {
    return canEdit(report)
  }

  function canSubmit(report: WeeklyReport) {
    return activeTab.value === "self" && report.status === "in_progress" && report.employee_id === authStore.user?.id
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
    void router.replace({ query: returnQuery.value })
    void loadReports()
  }

  onMounted(() => {
    syncRouteFilters()
    void Promise.all([loadReports(), loadGroups()])
  })
  watch(() => authStore.effectiveRole?.role_code, () => {
    reportList.resetPage()
    void loadReports()
  })
  watch(() => route.query, () => {
    const previousState = currentListState()
    syncRouteFilters()
    if (currentListState() !== previousState) void loadReports()
  }, { deep: true })
  return { activeTab, reports, isLoading, errorMessage, groups, filters, returnQuery, page, pageSize, total, totalPages, openCreateReport, switchTab, resetFilters, search, canEdit, canSubmit, canDelete, removeReport, submitOwnReport, changePage, confirmDialogOpen, confirmDialogBusy, confirmDialogAction, closeConfirmDialog, confirmReportAction, authStore, reportCopy, copyBusy, copyMessage, copyTitle, dailyDialogOpen, dailyDialogReport, dailyDialogTasks, openDailyDialog, closeDailyDialog, onDailySaved }
}

