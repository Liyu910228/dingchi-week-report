<script setup lang="ts">
import { computed } from "vue"
import { UserRound } from "lucide-vue-next"
import { formatDateTime } from "@/utils/date"
import type { TeamMemberSummary, TeamReportEntry } from "../types"
import { latestMemberUpdates, memberSubmissionStatus } from "../report-submission"
const props=defineProps<{members:TeamMemberSummary[];reports:TeamReportEntry[]}>()
defineEmits<{open:[employeeId:string]}>()
const labels={unwritten:'未填写',pending:'进行中',submitted:'已提交'}
const statuses=computed(()=>props.members.map(member=>({...member,status:memberSubmissionStatus(props.reports,member.employeeId)})))
const counts=computed(()=>({unwritten:statuses.value.filter(m=>m.status==='unwritten').length,pending:statuses.value.filter(m=>m.status==='pending').length,submitted:statuses.value.filter(m=>m.status==='submitted').length}))
const updates=computed(()=>latestMemberUpdates(props.reports,props.members))
</script>
<template>
 <article class="submission-panel">
  <header><h2>周报提交情况（{{counts.submitted}}/{{members.length}}）</h2><div class="submission-counts"><span v-for="(label,status) in labels" :key="status" :class="status">{{label}} {{counts[status]}} 人</span></div></header>
  <div class="submission-columns">
   <div class="submission-members">
    <button v-for="member in statuses" :key="member.employeeId" type="button" :aria-label="`${member.employeeName} ${labels[member.status]}`" @click="$emit('open',member.employeeId)">
     <span class="member-avatar" :class="member.status"><UserRound :size="25" /><i v-if="member.status==='submitted'">✓</i></span>
     <strong>{{member.employeeName}}</strong><small :class="member.status">{{labels[member.status]}}</small>
    </button><p v-if="!members.length" class="empty">暂无团队成员</p>
   </div>
   <section class="member-activity" aria-label="成员周报动态"><h3>成员周报动态</h3><div class="activity-scroll" tabindex="0">
    <button v-for="report in updates" :key="report.employeeId" type="button" @click="$emit('open',report.employeeId)"><span><strong>{{report.employeeName}}</strong> 更新了周报</span><time :datetime="report.updatedAt">{{formatDateTime(report.updatedAt)}}</time></button>
    <p v-if="!updates.length" class="empty">暂无周报更新</p>
   </div></section>
  </div>
 </article>
</template>
<style scoped src="./TeamSubmissionPanel.css"></style>
