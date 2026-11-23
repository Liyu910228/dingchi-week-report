<script setup lang="ts">
import ScrollableTabs from "@/components/navigation/ScrollableTabs.vue"
import { useRouter, useRoute } from "vue-router"
import { onMounted, ref, watch } from "vue"
import { useMonthlyPlanList } from "@/features/monthly-plan/useMonthlyPlanList"
import NoticeBridge from "@/components/feedback/NoticeBridge.vue"
import PaginationBar from "@/components/navigation/PaginationBar.vue"
import ConfirmDialog from "@/components/feedback/ConfirmDialog.vue"
import MonthlyPlanListHeader from "./components/MonthlyPlanListHeader.vue"
import MonthlyPlanFilters from "./components/MonthlyPlanFilters.vue"
import MonthlyPlanTable from "./components/MonthlyPlanTable.vue"
import MonthlyApprovalTable from "./components/MonthlyApprovalTable.vue"
import { useAuthStore } from "@/features/auth/store"
import CountBadge from "@/components/feedback/CountBadge.vue"
import { getAssignedApproval } from "@/features/monthly-plan/api"
import ApprovalSnapshotDialog from "./components/ApprovalSnapshotDialog.vue"
import type { ApprovalRecord } from "@/features/monthly-plan/types"

const list = useMonthlyPlanList()
const auth=useAuthStore()
const router=useRouter(),route=useRoute()
const deleting = ref("")
const deletingChange=ref(false)
function askDelete(id:string,change=false){deleting.value=id;deletingChange.value=change}
async function copyPlan(id:string){const planId=await list.copyPlan(id);if(planId)await router.push({name:"monthly-plan-edit",params:{planId},query:{tab:"mine"}})}
async function beginChange(id:string){const changeId=await list.beginChange(id);if(changeId)await router.push({name:"monthly-plan-change-new",params:{planId:changeId},query:{tab:list.activeTab.value}})}
const viewing = ref<ApprovalRecord|null>(null)
async function decide(record:ApprovalRecord,reject:boolean,reason:string){if(await list.decide(record,reject,reason))closeViewing()}
function closeViewing(){viewing.value=null;if(route.query.approval_id){const query={...route.query};delete query.approval_id;void router.replace({query})}}
async function openRequested(){
 const id=String(route.query.approval_id || '');if(!id)return
 if(list.activeTab.value!=='approvals'){list.activeTab.value='approvals';list.filters.page=1;await list.load()}
 try{const record=await getAssignedApproval(id);if(String(route.query.approval_id)===id)viewing.value=record}
 catch(cause){if(String(route.query.approval_id)===id)list.error.value=cause instanceof Error?cause.message:'审批记录加载失败。'}
}
watch(()=>route.query.approval_id,()=>void openRequested())
watch(()=>auth.effectiveRole?.role_code,closeViewing)
function search() { list.filters.page = 1; void list.load() }
function page(value: number) { list.filters.page = value; void list.load() }
function selectTab(tab: "mine" | "members" | "approvals" | "shared") {
  list.selectTab(tab)
  void router.replace({ query: { ...route.query, tab } })
}
async function remove() { const id = deleting.value; deleting.value = ""; await list.action(id, "delete", deletingChange.value) }
onMounted(async()=>{
 const tab=route.query.tab
 if(tab==='shared' || tab==='approvals' || (tab==='mine' && (auth.effectiveRole?.scope!=='all' || auth.reportingRoles.length)) || (tab==='members' && auth.effectiveRole?.scope!=='self'))list.activeTab.value=tab
 await list.initialize();await openRequested()
})
</script>
<template>
  <div class="monthly-plan-page">
    <section class="dashboard-card monthly-list-card" aria-label="月度计划列表">
    <MonthlyPlanListHeader :context="list.context.value" :personal="list.activeTab.value==='mine'">
    <ScrollableTabs :items="list.tabs.value.map(tab => ({id:tab.value,name:tab.label}))" :model-value="list.activeTab.value" aria-label="月度计划分类" tab-id-prefix="monthly-tab-" panel-id="monthly-tab-content" @update:model-value="selectTab($event as 'mine' | 'members' | 'approvals' | 'shared')"><template #suffix="{item}"><CountBadge v-if="item.id==='approvals'" :count="list.pendingCount.value" /></template></ScrollableTabs>
    </MonthlyPlanListHeader>
    <div id="monthly-tab-content" class="monthly-tab-content" role="tabpanel" :aria-labelledby="`monthly-tab-${list.activeTab.value}`">
    <MonthlyPlanFilters v-model="list.filters" :busy="list.busy.value" :view="list.activeTab.value" @search="search" />
    <NoticeBridge :warning-message="list.error.value" />
    <MonthlyApprovalTable v-if="list.activeTab.value==='approvals'" :records="list.data.value.approvals" :busy="list.busy.value" @view="viewing=$event" />
    <MonthlyPlanTable v-else :status-filter="list.appliedStatus.value" :items="list.data.value.items" :busy="list.busy.value" :view="list.activeTab.value" @submit="list.action($event, 'submit')" @delete="askDelete($event)" @copy="copyPlan" @change-create="beginChange" @change-submit="list.action($event, 'submit', true)" @change-delete="askDelete($event,true)" />
    <PaginationBar class="monthly-list-pagination" :page="list.data.value.page" :page-size="list.data.value.page_size" :total="list.data.value.total" :total-pages="list.data.value.total_pages" :disabled="list.busy.value" @change="page" />
    </div></section>
    <ApprovalSnapshotDialog :record="viewing" :busy="list.busy.value" :error="list.error.value" @close="closeViewing" @decide="decide" />
    <ConfirmDialog :open="Boolean(deleting)" title="删除月度计划" :message="deletingChange ? '确认删除此变更申请？原生效计划不受影响。' : '确认删除此月度计划？审批及变更历史会保留，相关月份将不能填写周报。'" @close="deleting = ''" @confirm="remove" />
  </div>
</template>
<style scoped src="./IndexView.css"></style>
