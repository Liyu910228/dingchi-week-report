<script setup lang="ts">
import type { ManagedMonthlyPlan } from "@/mobile/features/monthly-plan/types"
import { formatDateTime } from "@/utils/date"
import PlanStatusTag from "./PlanStatusTag.vue"
defineProps<{plan:ManagedMonthlyPlan;change?:boolean;status?:string;updatedAt?:string;rejectionReason?:string}>()
</script>
<template>
  <section class="dashboard-card plan-detail-heading">
    <div class="heading-main">
      <h1>{{plan.month_key}} 月度计划{{change?'变更':''}}</h1>
      <dl class="heading-meta">
        <div><dt>用户</dt><dd>{{plan.employee_name}}</dd></div>
        <div><dt>职位</dt><dd>{{plan.role_name || plan.role_code}}</dd></div>
        <div><dt>分组</dt><dd>{{plan.group_name || '未分组'}}</dd></div>
        <div><dt>更新时间</dt><dd>{{formatDateTime(updatedAt || plan.updated_at)}}</dd></div>
      </dl>
    </div>
    <PlanStatusTag class="heading-status" :status="status || plan.status" />
    <p v-if="rejectionReason" class="heading-reason">驳回原因：{{rejectionReason}}</p>
  </section>
</template>
<style scoped src="./PlanDetailHeading.css"></style>
