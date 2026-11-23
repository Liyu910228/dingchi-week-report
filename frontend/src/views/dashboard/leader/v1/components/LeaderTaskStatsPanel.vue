<script setup lang="ts">
import { progressColor } from "@/utils/progress-color"
import { computed, ref, watch } from "vue"
import { useRouter } from "vue-router"
import { ListChecks, UsersRound } from "lucide-vue-next"

import type { DashboardGroupStats, DashboardMemberStats } from "@/features/dashboard/types"

const props = defineProps<{
  groups: DashboardGroupStats[]
  members: DashboardMemberStats[]
  period: { start: string; end: string }
}>()

const router = useRouter()

const taskTotal = computed(() => props.members.reduce((sum, member) => sum + member.task_count, 0))

function taskPreview(member: DashboardMemberStats) {
  const names = member.tasks.map(task => task.detail_count
    ? `${task.task_name}（${task.completed_detail_count || 0}/${task.detail_count}，${Math.round(task.detail_completion_rate || 0)}%）`
    : task.task_name).filter(Boolean)
  if (!names.length) return "暂无任务名称"
  return names.slice(0, 3).join("、") + (names.length < member.task_count ? ` 等${member.task_count}项` : "")
}

function openMemberReports(member: DashboardMemberStats) {
  if (!member.employee_id) return
  void router.push({
    name: "weekly-reports",
    query: {
      employee_id: member.employee_id,
      period_start: props.period.start,
      period_end: props.period.end,
    },
  })
}

const selectedGroup = ref("")
function groupKey(group:DashboardGroupStats) { return group.group_id || `name:${group.group_name}` }
watch(()=>props.groups,groups=>{if(!groups.some(group=>groupKey(group)===selectedGroup.value))selectedGroup.value=groups[0]?groupKey(groups[0]):""},{immediate:true})
const visibleMembers=computed(()=>{
 const group=props.groups.find(group=>groupKey(group)===selectedGroup.value)
 return group?props.members.filter(member=>member.group_id!==undefined ? member.group_id===group.group_id : member.group_name===group.group_name):[]
})
</script>

<template>
  <section class="leader-task-stats-panel">
    <div class="leader-task-stats-heading">
      <div class="leader-section-title">
        <span class="leader-section-icon leader-section-icon--blue"><ListChecks :size="17" /></span>
        <h2>本周人员与团队任务</h2>
      </div>
      <span class="leader-task-stats-total">{{ taskTotal }} 项任务</span>
    </div>

    <div v-if="groups.length" class="leader-group-stats">
      <button
        v-for="group in groups"
        :key="group.group_id || group.group_name"
        class="leader-group-stat"
        :class="{ 'is-selected': selectedGroup===groupKey(group) }"
        :aria-pressed="selectedGroup===groupKey(group)"
        type="button"
        
        @click="selectedGroup=groupKey(group)"
      >
        <div class="leader-group-stat__title"><strong>{{ group.group_name }}</strong><b :style="{ color: progressColor(group.completion_rate) }">{{ Math.round(group.completion_rate) }}%</b></div>
        <div class="leader-group-stat__meta"><span><UsersRound :size="13" />{{ group.member_count }} 人</span><span><ListChecks :size="13" />{{ group.task_count }} 项任务</span></div>
        <div class="leader-group-stat__track"><i :style="{ background: progressColor(group.completion_rate), width: `${Math.min(100, Math.max(0, group.completion_rate))}%` }" /></div>
        <small>已完成 {{ group.completed_task_count }} · 进行中 {{ group.in_progress_task_count }} · 风险 {{ group.risk_task_count }}</small>
      </button>
    </div>

    <div v-if="groups.length" class="leader-member-stats" :key="selectedGroup">
      <div class="leader-member-stats__head"><span>人员</span><span>所属团队</span><span>本周任务</span><span>完成情况</span><span>进度</span></div>
      <button
        v-for="member in visibleMembers"
        :key="member.employee_id"
        class="leader-member-stat"
        :class="{ 'is-clickable': Boolean(member.employee_id) }"
        type="button"
        :disabled="!member.employee_id"
        @click="openMemberReports(member)"
      >
        <div class="leader-member-stat__person"><span>{{ member.employee_name.slice(0, 1) }}</span><div><strong>{{ member.employee_name }}</strong><small>{{ member.role_name }}</small></div></div>
        <span class="leader-member-stat__group">{{ member.group_name }}</span>
        <div class="leader-member-stat__tasks" :title="taskPreview(member)"><b>{{ member.task_count }} 项</b><small>{{ taskPreview(member) }}</small></div>
        <span class="leader-member-stat__result">完成 {{ member.completed_task_count }} · 风险 {{ member.risk_task_count }}</span>
        <div class="leader-member-stat__progress"><i :style="{ background: progressColor(member.progress_percent ?? member.completion_rate), width: `${Math.min(100, Math.max(0, (member.progress_percent ?? member.completion_rate)))}%` }" /><b :style="{ color: progressColor(member.progress_percent ?? member.completion_rate) }">{{ Math.round(member.progress_percent ?? member.completion_rate) }}%</b></div>
      </button>
      <div v-if="!visibleMembers.length" class="leader-task-stats-empty">该团队暂无需填写周报的人员</div>
    </div>
    <div v-if="!groups.length && !members.length" class="leader-task-stats-empty">本周暂无团队任务数据</div>
  </section>
</template>

<style scoped src="./LeaderTaskStatsPanel.css"></style>
