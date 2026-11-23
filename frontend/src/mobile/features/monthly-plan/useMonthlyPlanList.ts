import { computed, reactive, ref, watch } from "vue"
import { useTodoStore } from "@/mobile/features/todos/store"
import { useAuthStore } from "@/features/auth/store"
import { copyManagedPlan, decideManagedPlan, decidePlanChange,deletePlanChange,submitPlanChange, deleteManagedPlan, getPlanContext, listMonthlyPlans, submitManagedPlan } from "./api"
import type { ApprovalRecord, PlanContext, PlanFilters, PlanList, PlanListView } from "./types"

export function useMonthlyPlanList() {
  const auth=useAuthStore(),todos=useTodoStore()
  const pendingCount=computed(()=>todos.loaded?todos.data.pending_approval_count:(context.value?.pending_approval_count || 0))
  const activeTab=ref<PlanListView>(auth.effectiveRole?.scope==='all' && !auth.reportingRoles.length?'members':'mine')
  const hasApprovalTasks=ref(false)
  const appliedStatus=ref('')
  const tabs=computed(()=>[
    ...((auth.effectiveRole?.scope!=='all' || auth.reportingRoles.length)?[{value:'mine' as const,label:'我的月度计划'}]:[]),
    ...(auth.effectiveRole?.scope!=='self'?[{value:'members' as const,label:'团队月度计划'}]:[]),
    {value:'shared' as const,label:'共享月度计划'},
    ...((hasApprovalTasks.value || pendingCount.value>0)?[{value:'approvals' as const,label:'待审批'}]:[]),
  ])
  const filters = reactive<PlanFilters>({ role_code: "", month_key: "", status: "", employee_id: "", group_id: "", page: 1, page_size: 10 })
  const data = ref<PlanList>({ items: [], approvals: [], page: 1, page_size: 10, total: 0, total_pages: 0 })
  const context = ref<PlanContext | null>(null)
  const error = ref("")
  const busy = ref(false)
  let version = 0
  let appliedQuery: PlanFilters = {}
  async function load(append = false) {
    if (append && (busy.value || data.value.page >= data.value.total_pages)) return
    if (!auth.isAuthenticated) return
    const current = ++version
    busy.value = true
    error.value = ""
    try {
      const query = append ? {...appliedQuery, page:data.value.page + 1} : {...filters, page:1}
      const status=query.status || ''
      const result = await listMonthlyPlans({...query,view:activeTab.value})
      if (current === version) {
        appliedQuery=query;filters.page=result.page;appliedStatus.value=status
        data.value = append ? {...result,
          items:[...new Map([...data.value.items,...result.items].map(item=>[item.id,item])).values()],
          approvals:[...new Map([...data.value.approvals,...result.approvals].map(item=>[item.id,item])).values()],
        } : result
        hasApprovalTasks.value=Boolean(result.has_approval_tasks)
      }
    } catch (cause) { if (current === version) error.value = cause instanceof Error ? cause.message : "月度计划加载失败。" }
    finally { if (current === version) busy.value = false }
  }
  async function initialize() {
    if (!auth.isAuthenticated) return
    const token=auth.token
    await load()
    const current=version
    if (!auth.isAuthenticated || token!==auth.token) return
    try {
      const result=await getPlanContext()
      if(current!==version || token!==auth.token)return
      context.value=result;hasApprovalTasks.value=Boolean(result.has_approval_tasks)
    } catch (cause) {
      if(current===version && token===auth.token)error.value=cause instanceof Error?cause.message:"审批配置加载失败。"
    }
  }
  function selectTab(tab:PlanListView) {
    if(activeTab.value===tab)return
    activeTab.value=tab
    filters.employee_name='';filters.page=1;filters.role_code='';filters.status='';filters.employee_id='';filters.group_id=''
    void load()
  }
  async function decide(record:ApprovalRecord,reject:boolean,reason:string) {
    if(!record.plan_id)return false
    busy.value=true;error.value=''
    try {if(record.change_id)await decidePlanChange(record.change_id,reject?'reject':'approve',reason,record.id);else await decideManagedPlan(record.plan_id,reject?'reject':'approve',reason,record.id);await load();await todos.load();return true}
    catch(cause){error.value=cause instanceof Error?cause.message:'审批失败。';return false}
    finally{busy.value=false}
  }
  watch(()=>[auth.user?.id,auth.effectiveRole?.role_code],()=>{
    version++;context.value=null;hasApprovalTasks.value=false;error.value='';busy.value=false;appliedStatus.value=''
    data.value={items:[],approvals:[],page:1,page_size:10,total:0,total_pages:0}
    activeTab.value=auth.effectiveRole?.scope==='all' && !auth.reportingRoles.length?'members':'mine';filters.page=1
    if(auth.isAuthenticated)void initialize()
  })
  async function action(id: string, mode: "submit" | "delete", change=false) {
    busy.value = true
    error.value = ""
    try {
      if (mode === "submit") await (change?submitPlanChange(id):submitManagedPlan(id))
      else await (change?deletePlanChange(id):deleteManagedPlan(id))
      await load()
    } catch (cause) { error.value = cause instanceof Error ? cause.message : "操作失败。" }
    finally { busy.value = false }
  }
  async function beginChange(id:string) { return id }
  async function copyPlan(id: string) {
    busy.value = true; error.value = ""
    try { const result = await copyManagedPlan(id); await load(); return result.plan.id }
    catch (cause) { error.value = cause instanceof Error ? cause.message : "复制月度计划失败。"; return "" }
    finally { busy.value = false }
  }
  const loadMore = () => load(true)
  return { loadMore, copyPlan, appliedStatus, pendingCount, filters, data, context, error, busy, load, initialize, action, activeTab, tabs, selectTab, decide,beginChange }
}
