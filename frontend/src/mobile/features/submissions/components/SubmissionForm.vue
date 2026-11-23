<script setup lang="ts">
import DailyTaskSection from "@/mobile/features/weekly-report/components/DailyTaskSection.vue"
import {useCommonDailySummary} from '../useCommonDailySummary'
import TaskPreviewScope from "@/mobile/components/data-display/TaskPreviewScope.vue"
import {computed,onMounted} from "vue"
import {useRoute,useRouter,RouterLink} from "vue-router"
import WeekPeriodPicker from "@/mobile/components/form/WeekPeriodPicker.vue"
import AlertDialog from "@/mobile/components/feedback/AlertDialog.vue"
import NoticeBridge from "@/mobile/components/feedback/NoticeBridge.vue"
import ScrollableTabs from "@/mobile/components/navigation/ScrollableTabs.vue"
import UnsavedChangesGuard from "@/mobile/components/navigation/UnsavedChangesGuard.vue"
import PlanDetailHeading from "@/mobile/features/monthly-plan/components/PlanDetailHeading.vue"
import ApprovalTimeline from "@/mobile/features/monthly-plan/components/ApprovalTimeline.vue"
import PlanChangeHistory from "@/mobile/features/monthly-plan/components/PlanChangeHistory.vue"
import TaskProgressHistory from "@/mobile/features/monthly-plan/components/TaskProgressHistory.vue"
import PlanComparison from "@/mobile/features/monthly-plan/components/PlanComparison.vue"
import ChangeReasonPanel from "./ChangeReasonPanel.vue"
import MonthlyFloatingPanels from "./MonthlyFloatingPanels.vue"
import {planStatusLabels} from "@/mobile/features/monthly-plan/types"
import {useAuthStore} from "@/features/auth/store"
import {monthlyBodies,weeklyBodies} from "../template-registry"
import {useSubmissionEditor} from "../useSubmissionEditor"
import type {SubmissionKind,SubmissionPart,MonthlyPayload} from "../types"
import SubmissionWeeklyReadonly from "./SubmissionWeeklyReadonly.vue"
import SubmissionWeeklyHeading from "./SubmissionWeeklyHeading.vue"
const props=defineProps<{kind:SubmissionKind;readonly?:boolean}>()
const route=useRoute(),router=useRouter(),auth=useAuthStore(),editor=useSubmissionEditor(props.kind,Boolean(props.readonly))
const commonDaily=useCommonDailySummary(editor.input)
const periodEnd=computed(()=>{const value=new Date(`${editor.input.period_start}T00:00:00`);value.setDate(value.getDate()+6);return `${value.getFullYear()}-${String(value.getMonth()+1).padStart(2,"0")}-${String(value.getDate()).padStart(2,"0")}`})
const back=computed(()=>props.kind==='monthly'?'mobile-monthly-plans':'mobile-weekly-reports')
const editable=computed(()=>!props.readonly && editor.canEdit.value)
async function save(submit:boolean){const id=await editor.save(submit);if(!id)return;const prefix=props.kind==='monthly'?'monthly-plan':'weekly-report';await router.replace({name:editor.change.value?`mobile-monthly-plan-change-${submit?'detail':'edit'}`:`mobile-${prefix}-${submit?'detail':'edit'}`,params:editor.change.value?{changeId:id}:props.kind==='monthly'?{planId:id}:{reportId:id}})}
function update(part:SubmissionPart,payload:SubmissionPart['payload']){editor.update(part,{...payload,daily_tasks:part.payload.daily_tasks})}
function canUpdateProgress(part:SubmissionPart){const plan=editor.detail.value?.plan;return Boolean(plan && !editor.change.value && plan.employee_id===auth.user?.id && plan.role_codes.includes(part.role_code))}
function updateLiveMonthly(part:SubmissionPart,payload:MonthlyPayload){if(part.monthly_plan)part.monthly_plan.tasks=payload.tasks;if(part.detail?.monthly_plan_tasks)part.detail.monthly_plan_tasks=payload.tasks}
async function beginChange(){if(editor.detail.value)await router.push({name:"mobile-monthly-plan-change-new",params:{planId:editor.detail.value.plan.id}})}
function baseline(part:SubmissionPart){const before=editor.change.value?.base_snapshot.parts.find(p=>p.role_code===part.role_code);return before?{...before.payload,template_code:before.template_code,month_key:editor.input.month_key}:undefined}
onMounted(()=>{if(props.kind==='weekly' && !route.params.reportId && typeof route.query.period_start==='string' && /^\d{4}-\d{2}-\d{2}$/.test(route.query.period_start))editor.input.period_start=route.query.period_start;void editor.load(String(route.params.planId || route.params.reportId || ''),String(route.params.changeId || ''),route.name==='mobile-monthly-plan-change-new')})
</script>
<template>
<div class="submission-form">
 <Teleport defer to="#weekly-report-header-actions"><div class="submission-actions"><RouterLink v-if="readonly && kind=== 'monthly' && editor.detail.value?.can_edit" class="ghost-button" :to="{name:kind==='monthly'?'mobile-monthly-plan-edit':'mobile-weekly-report-edit',params:kind==='monthly'?{planId:editor.detail.value.plan.id}:{reportId:editor.detail.value.plan.id}}">编辑</RouterLink><button v-if="readonly && kind==='monthly' && editor.detail.value?.plan.can_create_change && editor.detail.value.plan.employee_id===auth.user?.id" class="primary-button submission-change-button" :disabled="editor.busy.value" @click="beginChange">申请变更</button><template v-if="editable && !editor.unavailable.value"><button class="ghost-button" :disabled="editor.busy.value" @click="save(false)">保存草稿</button><button class="primary-button" :disabled="editor.busy.value" @click="save(true)">{{kind==='monthly'?'提交审批':'提交周报'}}</button></template></div></Teleport>
 <UnsavedChangesGuard :dirty="editor.unsaved.hasChanges.value" :enabled="editable" :reset-key="editor.unsaved.resetKey.value" />
 <div v-if="editor.loading.value" class="dashboard-card">正在加载…</div>
 <AlertDialog v-else-if="editor.unavailable.value" open title="无法填写" :message="editor.error.value" @close="router.replace({name:back})" />
 <template v-else>
 <NoticeBridge :warning-message="editor.error.value" />
 <SubmissionWeeklyHeading v-if="kind==='weekly' && readonly && editor.detail.value" :report="editor.detail.value.plan"><template #actions><RouterLink v-if="editor.detail.value.can_edit" class="weekly-heading-edit" :to="{name:'mobile-weekly-report-edit',params:{reportId:editor.detail.value.plan.id}}">编辑</RouterLink></template></SubmissionWeeklyHeading>
 <section v-if="kind==='weekly' && !readonly" class="dashboard-card submission-period submission-period--weekly" :inert="editor.busy.value"><label>周报周期<WeekPeriodPicker :start="editor.input.period_start || ''" :end="periodEnd" :disabled="!editable" @update:start="editor.input.period_start=$event" /></label><label v-if="kind==='weekly'">所属月度<input :value="editor.input.period_start?.slice(0,7) || editor.input.month_key" readonly /></label><div v-if="editor.detail.value" class="submission-period-meta"><span>{{editor.detail.value.plan.role_name}}</span><span>{{editor.detail.value.plan.employee_name}} · {{planStatusLabels[editor.detail.value.plan.status] || ({in_progress:'进行中',not_started:'待开始',completed:'已完成'}[editor.detail.value.plan.status as 'in_progress']) || editor.detail.value.plan.status}}</span></div></section>
 <div class="submission-layout" :inert="editor.busy.value" :aria-busy="editor.busy.value" :class="{'submission-layout--monthly':kind==='monthly'}">
 <div class="submission-positions">
 <template v-if="kind==='monthly'">
 <PlanDetailHeading v-if="editor.change.value || editor.detail.value" :plan="(editor.change.value?.plan || editor.detail.value!.plan)" :change="Boolean(editor.change.value)" :status="editor.change.value?.change.status" :updated-at="editor.change.value?.change.updated_at" :rejection-reason="editor.change.value?.change.rejection_reason || editor.detail.value?.plan.rejection_reason" />
 <section v-else class="dashboard-card submission-period" :inert="editor.busy.value"><label class="submission-month"><span>所属月度<span class="required" aria-hidden="true"> *</span></span><input type="month" v-model="editor.input.month_key" required aria-required="true" :disabled="!editable" /></label></section>
 </template>
 <div class="dashboard-card submission-position-workspace"><div class="submission-position-tabs"><ScrollableTabs v-model="editor.active.value" :items="editor.tabs.value" aria-label="填报职位" /></div>
 <section v-for="part in editor.input.parts" :key="`${part.role_code}:${editor.generation.value}`" v-show="editor.active.value===part.role_code" class="submission-template" :aria-label="part.role_name">
 <PlanComparison v-if="readonly && editor.change.value && baseline(part)" :before="baseline(part)!" :after="{...part.payload,template_code:part.template_code,month_key:editor.input.month_key}" />
 <component v-if="kind==='monthly'" :is="monthlyBodies[part.template_code]" :part="part" :month-key="editor.input.month_key" :readonly="!editable" :progress-editable="canUpdateProgress(part)" @update:payload="update(part,$event)" />
 <template v-else>
 <TaskPreviewScope :limit="3"><component v-if="part.monthly_plan?.plan" :is="monthlyBodies[part.template_code]" :part="{...part,payload:{summary:part.monthly_plan.plan.summary,tasks:part.monthly_plan.tasks}}" :month-key="editor.input.period_start?.slice(0,7) || ''" readonly :progress-editable="canUpdateProgress(part)" @update:payload="updateLiveMonthly(part,$event)" /></TaskPreviewScope>
 <NoticeBridge v-if="editable && editor.active.value===part.role_code && part.monthly_approved===false" :warning-message="part.monthly_message || `「${part.role_name}」：请先完成所属月度的月度计划审批。`" />
 <component v-if="editable" :is="weeklyBodies[part.template_code]" :part="part" :period-start="editor.input.period_start || ''" @update:payload="update(part,{...part.payload,...$event})" />
 <SubmissionWeeklyReadonly v-else :part="part" />
 </template>
 </section>
 </div>
 <DailyTaskSection v-if="kind==='weekly'" :report="commonDaily.report.value" :daily-tasks="commonDaily.tasks.value" :can-edit="editable" :defer-save="editable" @update:daily-tasks="commonDaily.update" />
 <TaskProgressHistory v-if="readonly && !editor.change.value && editor.detail.value?.progress_history?.length" :entries="editor.detail.value.progress_history" />
 <PlanChangeHistory v-if="readonly && !editor.change.value && editor.detail.value?.history" :history="editor.detail.value.history" />
 </div>
 <MonthlyFloatingPanels v-if="kind==='monthly'" :has-reason="Boolean(editor.change.value)" :busy="editor.busy.value">
 <template #approval><ApprovalTimeline :managers="editor.change.value?.managers || editor.context.value?.managers || editor.detail.value?.managers" :plan="editor.change.value?{...editor.change.value.plan,...editor.change.value.change}:editor.detail.value?.plan" :record="editor.change.value?.approvals?.[0] || editor.detail.value?.approvals?.[0]" :applicant="editor.detail.value?.plan.employee_name || editor.change.value?.plan.employee_name || auth.user?.display_name" /></template>
 <template #reason><ChangeReasonPanel v-if="editor.change.value" v-model="editor.input.change_reason" :readonly="!editable" :disabled="editor.busy.value" /></template>
 </MonthlyFloatingPanels>
 </div>
 </template>
</div>
</template>
<style scoped src="./SubmissionForm.css"></style>







