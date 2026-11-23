<script setup lang="ts">
import { vRowBackgrounds } from "@/shared/table/row-backgrounds"
import { vResizableColumns } from "@/shared/table/resizable-columns"
import { useUserTableResizeKey } from "@/features/auth/useUserTableResizeKey"
import MonthlyGoalSummary from "@/features/monthly-plan/components/MonthlyGoalSummary.vue"
import PlanStatusTag from "@/features/monthly-plan/components/PlanStatusTag.vue"
import { ref,watch } from "vue"
import { RouterLink } from "vue-router"
import { useAuthStore } from "@/features/auth/store"
import { type ManagedMonthlyPlan, type PlanListView } from "@/features/monthly-plan/types"
import { formatDateTime } from "@/utils/date"
const props=defineProps<{items:ManagedMonthlyPlan[];busy:boolean;view:PlanListView;statusFilter?:string}>()
defineEmits<{copy:[id:string];submit:[id:string];delete:[id:string];changeCreate:[id:string];changeSubmit:[id:string];changeDelete:[id:string]}>()
const auth=useAuthStore(),expanded=ref<Record<string,boolean>>({})
function visibleChildren(plan:ManagedMonthlyPlan){return (plan.children || []).filter(child=>!props.statusFilter || child.status===props.statusFilter)}
function isExpanded(plan:ManagedMonthlyPlan){return expanded.value[plan.id] ?? (props.statusFilter ? visibleChildren(plan).length>0 : (plan.children || []).some(child=>child.status==='pending'))}
function toggle(plan:ManagedMonthlyPlan){expanded.value={...expanded.value,[plan.id]:!isExpanded(plan)}}
watch(()=>[props.items,props.statusFilter],()=>{expanded.value={}})
function own(plan:ManagedMonthlyPlan) { return plan.employee_id===auth.user?.id && auth.roles.some(role=>role.role_code===plan.role_code) && plan.status!=='pending' }
const resizeKey = useUserTableResizeKey(() => `monthly-plan:${props.view}`)
</script>
<template>
  <div class="monthly-table-wrap">
    <table v-row-backgrounds v-resizable-columns="resizeKey" class="monthly-table" :class="{'is-personal':view==='mine'}"><thead><tr><th data-column-key="month_key">月份</th><th data-column-key="role_code">职位</th><th v-if="view!=='mine'" data-column-key="employee_name">人员</th><th v-if="view!=='mine'" data-column-key="group_name">分组</th><th data-column-key="summary">月度目标</th><th data-column-key="status">审批状态</th><th data-column-key="updated_at">更新日期</th><th data-column-key="actions">操作</th></tr></thead>
      <tbody><template v-for="plan in items" :key="plan.id"><tr :class="{'is-pending':plan.status==='pending'}"><td><span class="month-value"><span class="month-toggle-slot"><button v-if="visibleChildren(plan).length" class="tree-toggle" type="button" aria-label="展开或收起变更申请" :aria-expanded="isExpanded(plan)" @click="toggle(plan)">{{isExpanded(plan)?'▾':'▸'}}</button></span><span>{{plan.month_key}}</span></span></td><td>{{plan.role_name || plan.role_code}}</td><td v-if="view!=='mine'">{{plan.employee_name}}</td><td v-if="view!=='mine'">{{plan.group_name}}</td><td class="summary"><MonthlyGoalSummary :summary="plan.summary" :sections="plan.role_summaries" /></td><td><PlanStatusTag :status="plan.status" /></td><td>{{formatDateTime(plan.updated_at)}}</td><td class="actions"><RouterLink :to="{name:'monthly-plan-detail',params:{planId:plan.id},query:{tab:view}}">查看</RouterLink><template v-if="view === 'mine' && own(plan)"><button v-if="plan.status==='approved'" type="button" :disabled="busy" @click="$emit('copy',plan.id)">复制</button><button v-if="plan.can_create_change" :disabled="busy" @click="$emit('changeCreate',plan.id)">申请变更</button><RouterLink v-if="plan.status!=='approved'" :to="{name:'monthly-plan-edit',params:{planId:plan.id},query:{tab:view}}">修改</RouterLink><button v-if="plan.status==='draft'" type="button" :disabled="busy" @click="$emit('submit',plan.id)">提交审批</button><button v-if="plan.status==='draft' && !plan.children?.some(child=>['draft','pending','rejected'].includes(child.status))" type="button" :disabled="busy" class="danger" @click="$emit('delete',plan.id)">删除</button></template></td></tr><template v-if="isExpanded(plan)"><tr v-for="child in visibleChildren(plan)" :key="child.id" class="change-row" data-row-kind="change" :data-row-state="child.status" :class="{'is-pending':child.status==='pending'}"><td>↳ 变更申请</td><td>{{plan.role_name || plan.role_code}}</td><td v-if="view!=='mine'">{{plan.employee_name}}</td><td v-if="view!=='mine'">{{plan.group_name}}</td><td class="summary"><MonthlyGoalSummary :summary="child.summary" :sections="child.role_summaries" /></td><td><PlanStatusTag :status="child.status" /></td><td>{{formatDateTime(child.updated_at)}}</td><td class="actions"><RouterLink :to="{name:'monthly-plan-change-detail',params:{changeId:child.id},query:{tab:view}}">查看</RouterLink><template v-if="view==='mine' && own(plan) && ['draft','rejected'].includes(child.status)"><RouterLink :to="{name:'monthly-plan-change-edit',params:{changeId:child.id},query:{tab:view}}">修改</RouterLink><button v-if="child.status==='draft'" :disabled="busy" @click="$emit('changeSubmit',child.id)">提交审批</button><button class="danger" :disabled="busy" @click="$emit('changeDelete',child.id)">删除</button></template></td></tr></template></template>
      <tr v-if="busy && !items.length"><td class="empty-row" :colspan="view==='mine'?6:8">正在加载月度计划…</td></tr><tr v-else-if="!items.length"><td class="empty-row" :colspan="view==='mine'?6:8">暂无月度计划</td></tr></tbody>
    </table>
  </div>
</template>
<style scoped src="./MonthlyPlanTable.css"></style>
