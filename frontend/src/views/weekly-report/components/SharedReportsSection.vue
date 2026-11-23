<script setup lang="ts">
import { onMounted, reactive, ref } from "vue"
import NoticeBridge from "@/components/feedback/NoticeBridge.vue"
import ReportPagination from "@/features/weekly-report/components/ReportPagination.vue"
import { useReportList } from "@/features/weekly-report/composables/useReportList"
import { listUserOptions } from "@/features/directory/api"
import type { DirectoryUserOption } from "@/features/directory/types"
import ReportFilterBar from "./ReportFilterBar.vue"
import ReportListTable from "./ReportListTable.vue"

const list = useReportList()
const users = ref<DirectoryUserOption[]>([])
const optionError = ref("")
const filters = reactive({ month_key: "", period_start: "", period_end: "", role_code: "", employee_id: "" })
function load() { return list.load({ ...filters, view: "shared" }) }
function search() { list.resetPage(); void load() }
function reset() { Object.assign(filters, { month_key: "", period_start: "", period_end: "", role_code: "", employee_id: "" }); search() }
function page(value: number) { list.setPage(value); void load() }
onMounted(() => {
 void load()
 void listUserOptions().then(data => { users.value = data.items }).catch(cause => {
  optionError.value = cause instanceof Error ? cause.message : "人员选项加载失败。"
 })
})
</script>
<template>
<section class="dashboard-card shared-report-card" aria-label="共享周报">

 <ReportFilterBar v-model:month-key="filters.month_key" v-model:period-start="filters.period_start" v-model:period-end="filters.period_end" v-model:role-code="filters.role_code" v-model:employee-id="filters.employee_id" :user-options="users" show-person @search="search" @reset="reset" />
 <NoticeBridge :warning-message="list.errorMessage.value || optionError" />
 <ReportListTable @restored="load" :reports="list.reports.value" scope="all" :is-loading="list.isLoading.value" :return-query="{tab:'shared'}" empty-message="暂无共享周报" />
 <ReportPagination :page="list.page.value" :page-size="list.pageSize.value" :total="list.total.value" :total-pages="list.totalPages.value" :disabled="list.isLoading.value" @change="page" />
</section>
</template>
<style scoped src="./SharedReportsSection.css"></style>
