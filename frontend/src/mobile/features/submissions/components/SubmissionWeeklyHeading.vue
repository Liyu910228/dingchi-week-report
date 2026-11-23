<script setup lang="ts">
import {formatDateTime,formatPeriod} from "@/utils/date"
defineProps<{report:{employee_name?:string;role_name?:string;month_key:string;period_start?:string|null;period_end?:string|null;status:string;updated_at?:string|null}}>()
const labels:Record<string,string>={not_started:"待开始",in_progress:"进行中",completed:"已完成"}
</script>
<template>
 <section class="dashboard-card weekly-detail-heading" aria-label="周报信息">
  <div class="weekly-heading-top">
   <div class="weekly-heading-owner"><h1>{{report.employee_name || '周报'}}</h1><p>{{report.role_name || '—'}}</p></div>
   <div class="weekly-heading-actions"><slot name="actions" /></div>
  </div>
  <div class="weekly-heading-period"><span>周报周期</span><strong>{{formatPeriod(report.period_start,report.period_end)}}</strong></div>
  <div class="weekly-heading-bottom"><span class="weekly-heading-month">所属月度 <span>{{report.month_key}}</span></span><span class="weekly-heading-status" :class="`weekly-heading-status--${report.status}`">{{labels[report.status] || report.status}}</span></div>
  <div class="weekly-heading-updated">更新于 {{formatDateTime(report.updated_at)}}</div>
 </section>
</template>
<style scoped src="./SubmissionWeeklyHeading.css"></style>

