<script setup lang="ts">
import MonthlyGoalSummary from "@/mobile/features/monthly-plan/components/MonthlyGoalSummary.vue"
import PlanStatusTag from "@/mobile/features/monthly-plan/components/PlanStatusTag.vue"
import type { ApprovalRecord } from "@/mobile/features/monthly-plan/types"
import { formatDateTime } from "@/utils/date"
defineProps<{ records: ApprovalRecord[]; busy: boolean }>()
defineEmits<{ view: [record: ApprovalRecord] }>()
</script>
<template>
  <div class="approval-cards" aria-label="月度计划审批列表" :aria-busy="busy">
    <article v-for="record in records" :key="record.id" class="approval-card" :aria-label="`${record.month_key} ${record.employee_name}的申请`">
      <header class="approval-card-heading"><h2>{{record.month_key}} 月度计划</h2><PlanStatusTag :status="record.status" /></header>
      <dl class="approval-card-fields">
        <div><dt>提交人</dt><dd>{{record.employee_name || '—'}}</dd></div>
        <div><dt>职位</dt><dd>{{record.role_name || record.role_code || '—'}}</dd></div>
        <div><dt>分组</dt><dd>{{record.group_name || '—'}}</dd></div>
        <div><dt>申请类型</dt><dd>{{record.process_type==='change'?'变更申请':'首次申请'}} · 版本 {{record.revision}}</dd></div>
        <div><dt>月度目标</dt><dd><details class="approval-goal"><summary><span class="show-label">展开</span><span class="hide-label">收起</span></summary><MonthlyGoalSummary :summary="record.snapshot.summary" :sections="record.snapshot.parts?.map(part => ({role_code:part.role_code,role_name:part.role_name,summary:part.payload.summary || ''}))" /></details></dd></div>
        <div><dt>提交时间</dt><dd>{{formatDateTime(record.created_at)}}</dd></div>
        <div><dt>处理时间</dt><dd>{{formatDateTime(record.completed_at)}}</dd></div>
      </dl>
      <footer class="approval-card-actions"><button type="button" @click="$emit('view',record)">查看</button></footer>
    </article>
    <p v-if="!records.length" class="approval-empty" role="status">{{busy?'正在加载审批任务…':'暂无符合条件的审批任务'}}</p>
  </div>
</template>
<style scoped src="./MonthlyApprovalCards.css"></style>
