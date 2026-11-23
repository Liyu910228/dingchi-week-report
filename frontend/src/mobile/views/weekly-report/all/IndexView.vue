<script setup lang="ts">
import { computed, onMounted, reactive, watch } from "vue"
import { useRoute } from "vue-router"

import { useDirectoryFilterOptions } from "@/mobile/features/directory/useDirectoryFilterOptions"
import { useAuthStore } from "@/features/auth/store"
import { useReportList } from "@/mobile/features/weekly-report/composables/useReportList"
import type { ReportListFilters, WeeklyReport } from "@/mobile/features/weekly-report/types"
import NoticeBridge from "@/mobile/components/feedback/NoticeBridge.vue"

import ReportFilterBar from "../components/ReportFilterBar.vue"
import ReportListTable from "../components/ReportListTable.vue"
import ScrollLoadMore from "@/mobile/components/navigation/ScrollLoadMore.vue"

const authStore = useAuthStore()
const route = useRoute()
const reportList = useReportList()
const directory=useDirectoryFilterOptions()
const {groups,users}=directory
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
const errorMessage = computed(() => reportList.errorMessage.value || directory.error.value)
const page = computed(() => reportList.page.value)
const pageSize = computed(() => reportList.pageSize.value)
const total = computed(() => reportList.total.value)
const totalPages = computed(() => reportList.totalPages.value)

function queryFilters(): ReportListFilters {
  return {
    role_code: filters.role_code || undefined,
    month_key: filters.month_key || undefined,
    period_start: filters.period_start || undefined,
    period_end: filters.period_end || undefined,
    group_id: filters.group_id || undefined,
    employee_id: filters.employee_id || undefined,
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
  filters.group_id = ""
  filters.employee_id = ""
  search()
}

function changePage(page: number) {
  reportList.setPage(page)
  void loadReports()
}

function cannotEditOrDelete(_report: WeeklyReport) {
  return false
}

onMounted(() => {
  syncRouteFilters()
  void Promise.all([loadReports(), directory.load()])
})
watch(() => authStore.effectiveRole?.role_code, () => {
  reportList.resetPage()
  void loadReports()
})
watch(() => route.query, () => {
  syncRouteFilters()
  reportList.resetPage()
  void loadReports()
}, { deep: true })
</script>

<template>
  <div class="weekly-report-page">
    <NoticeBridge :warning-message="errorMessage" />

    <section class="dashboard-card report-list-card">

      <ReportFilterBar
        v-model:role-code="filters.role_code"
        v-model:month-key="filters.month_key"
        v-model:period-start="filters.period_start"
        v-model:period-end="filters.period_end"
        v-model:group-id="filters.group_id"
        :group-options="groups"
        v-model:employee-id="filters.employee_id"
        :user-options="users"
        show-person
        show-group
        @reset="resetFilters"
        @search="search"
      />
      <ReportListTable
        @restored="changePage(page)"
        :reports="reports"
        scope="all"
        :is-loading="isLoading"
        :can-edit="cannotEditOrDelete"
        :can-delete="cannotEditOrDelete"
        empty-message="暂无符合条件的周报"
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
  </div>
</template>

<style scoped src="./IndexView.css"></style>
