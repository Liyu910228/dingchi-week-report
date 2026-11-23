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

  let version = 0
  let loadedPage = 0
  let appliedFilters: ReportListFilters = {}
  async function load(filters: ReportListFilters = {}) {
    const append = loadedPage > 0 && page.value === loadedPage + 1
    if(append && isLoading.value)return
    const current = ++version
    const requestedPage = append ? loadedPage + 1 : 1
    const query = append ? appliedFilters : {...filters}
    isLoading.value = true
    errorMessage.value = ""
    try {
      const response = await listReports({...query, page:requestedPage, page_size:pageSize.value})
      if(current !== version)return
      reports.value = append
        ? [...new Map([...reports.value,...response.items].map(report=>[report.id,report])).values()]
        : response.items
      appliedFilters=query;loadedPage=response.page
      page.value=response.page;pageSize.value=response.page_size
      total.value=response.total;totalPages.value=response.total_pages
    } catch (error) {
      if(current !== version)return
      errorMessage.value=error instanceof Error ? error.message : "周报列表加载失败。"
      page.value=loadedPage || 1
      if(!append){reports.value=[];total.value=0;totalPages.value=0;loadedPage=0}
    } finally {if(current === version)isLoading.value=false}
  }

  function setPage(value: number) {
    if (isLoading.value) return
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
