import { ref } from "vue"

import { listReports } from "../api"
import type { ReportListFilters, WeeklyReport } from "../types"

export function useReportList() {
  const reports = ref<WeeklyReport[]>([])
  const page = ref(1)
  const pageSize = ref(10)
  const total = ref(0)
  const totalPages = ref(0)
  const isLoading = ref(false)
  const errorMessage = ref("")

  async function load(filters: ReportListFilters = {}) {
    isLoading.value = true
    errorMessage.value = ""
    try {
      const response = await listReports({
        page: page.value,
        page_size: pageSize.value,
        ...filters,
      })
      reports.value = response.items
      page.value = response.page
      pageSize.value = response.page_size
      total.value = response.total
      totalPages.value = response.total_pages
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : "周报列表加载失败。"
      reports.value = []
      total.value = 0
      totalPages.value = 0
    } finally {
      isLoading.value = false
    }
  }

  function setPage(value: number) {
    if (value < 1 || (totalPages.value > 0 && value > totalPages.value)) return
    page.value = value
  }

  function resetPage() {
    page.value = 1
  }

  return {
    reports,
    page,
    pageSize,
    total,
    totalPages,
    isLoading,
    errorMessage,
    load,
    setPage,
    resetPage,
  }
}
