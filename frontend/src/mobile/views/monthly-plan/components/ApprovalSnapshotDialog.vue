<script setup lang="ts">
import { computed,ref,watch } from "vue"
import SubmissionSnapshotTabs from "@/mobile/features/submissions/components/SubmissionSnapshotTabs.vue"
import PlanComparison from "@/mobile/features/monthly-plan/components/PlanComparison.vue"
import BaseDialog from "@/mobile/components/overlay/BaseDialog.vue"
import MonthlyPlanTaskPanel from "@/mobile/features/monthly-plan/components/MonthlyPlanTaskPanel.vue"
import type { ApprovalRecord } from "@/mobile/features/monthly-plan/types"
import { formatDateTime } from "@/utils/date"
import { clearFieldValidity, reportFormValidity } from "@/utils/form-validation"
import PlanStatusTag from "@/mobile/features/monthly-plan/components/PlanStatusTag.vue"
const props=defineProps<{record:ApprovalRecord|null;busy?:boolean;error?:string}>()
const emit=defineEmits<{close:[];decide:[record:ApprovalRecord,reject:boolean,reason:string]}>()
const fullContent=ref(false)
const reason=ref(''),form=ref<HTMLFormElement|null>(null)
const rejectionReason=computed(()=>props.record?.status==='rejected' ? props.record.steps.find(step=>step.status==='rejected')?.reason || '—' : '')
watch(()=>props.record,()=>{fullContent.value=false;reason.value='';const field=form.value?.querySelector('textarea');if(field){field.required=false;field.setCustomValidity('')}})
function submit(reject:boolean){
 if(props.busy || !props.record?.can_approve)return
 const field=form.value?.querySelector('textarea')
 if(!field)return
 field.required=reject
 field.setCustomValidity('')
 if(reportFormValidity(form.value))emit('decide',props.record,reject,reason.value.trim())
}
</script>
<template>
<BaseDialog :open="Boolean(record)" title="审批计划" :busy="busy" width="min(1440px, 96vw)" height="90dvh" @close="$emit('close')">
 <div v-if="record" class="approval-snapshot">
  <dl class="approval-meta" aria-label="申请信息"><div><dt>申请人</dt><dd>{{record.employee_name || '—'}}</dd></div><div><dt>所属月度</dt><dd>{{record.month_key || record.snapshot.month_key || '—'}}</dd></div><div class="approval-meta-wide"><dt>职位</dt><dd>{{record.role_name || record.role_code || '—'}}</dd></div><div><dt>分组</dt><dd>{{record.group_name || '未分组'}}</dd></div><div class="approval-meta-wide"><dt>提交时间</dt><dd><time :datetime="record.created_at">{{formatDateTime(record.created_at)}}</time></dd></div><div><dt>审批状态</dt><dd><PlanStatusTag :status="record.status" /></dd></div></dl>
  <div v-if="record.status==='rejected'" class="approval-rejection"><strong>驳回原因</strong><p>{{rejectionReason}}</p></div>
  <div v-if="record.process_type==='change'" class="approval-change-reason"><strong>变更原因</strong><p>{{record.snapshot.change_reason || '—'}}</p></div>
  <SubmissionSnapshotTabs v-if="record.snapshot.parts" :snapshot="record.snapshot" :baseline="record.base_snapshot" collapse-full />
  <template v-else>
  <PlanComparison v-if="record.base_snapshot" :before="record.base_snapshot" :after="record.snapshot" />
  <div v-if="record.base_snapshot" class="full-application-action"><button type="button" class="ghost-button" :aria-expanded="fullContent" aria-controls="legacy-full-application" @click="fullContent=!fullContent">{{fullContent?'收起完整申请内容':'查看完整申请内容'}}</button></div>
  <section v-if="!record.base_snapshot || fullContent" id="legacy-full-application" class="full-application" :class="{'full-application--expanded':record.base_snapshot}"><h3 v-if="record.base_snapshot">本次变更申请完整内容</h3><section class="snapshot-goal"><h2>月度目标</h2><p>{{record.snapshot.summary}}</p></section><MonthlyPlanTaskPanel :tasks="record.snapshot.tasks" :month-key="record.month_key || record.snapshot.month_key" :template-code="record.snapshot.template_code" readonly /></section></template>
  <p v-if="error" class="approval-error" role="alert">{{error}}</p>
  <form v-if="record.can_approve" id="monthly-plan-approval-form" ref="form" class="approval-decision" novalidate @input.capture="clearFieldValidity" @submit.prevent><label>审批意见（驳回必填）<textarea class="user-content" v-model="reason" maxlength="2000" rows="4" :disabled="busy" /></label></form>
 </div>
 <template v-if="record?.can_approve" #actions><button class="ghost-button" type="button" :disabled="busy" @click="submit(false)">通过</button><button class="ghost-button" type="button" :disabled="busy" @click="submit(true)">驳回</button></template>
</BaseDialog>
</template>
<style scoped src="./ApprovalSnapshotDialog.css"></style>


