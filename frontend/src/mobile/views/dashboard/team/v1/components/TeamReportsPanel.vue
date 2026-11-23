<script setup lang="ts">
import { progressColor } from "@/mobile/utils/progress-color"
import { computed } from "vue"
import { useRouter } from "vue-router"
import { ArrowRight, Target, UserRound } from "lucide-vue-next"

import type { DashboardMemberStats, DashboardTeamTask } from "@/mobile/features/dashboard/types"
import type { TeamMemberSummary, TeamPlanEntry, TeamReportEntry } from "../types"

import TeamSubmissionPanel from "./TeamSubmissionPanel.vue"

const props = defineProps<{
  reports: TeamReportEntry[]
  members: TeamMemberSummary[]
  memberStats: DashboardMemberStats[]
  tasks: DashboardTeamTask[]
  plans: TeamPlanEntry[]
  period: { start: string; end: string }
}>()

const router = useRouter()
const taskMap = computed(() => new Map(props.tasks.map((task) => [task.id, task])))
const focusTasks = computed(() => props.memberStats.flatMap((member) => member.tasks.map((task) => ({ member, task, detail: taskMap.value.get(task.id) }))).slice(0, 5))

function openMemberReports(employeeId: string) {
  if (!employeeId) return
  void router.push({ name: "mobile-weekly-reports", query: { employee_id: employeeId, period_start: props.period.start, period_end: props.period.end } })
}

function openAllReports() {
  void router.push({ name: "mobile-weekly-reports", query: { period_start: props.period.start, period_end: props.period.end } })
}
</script>

<template>
  <section class="team-execution-grid">
    <div class="team-execution-column team-execution-column--left">
      <TeamSubmissionPanel :members="members" :reports="reports" @open="openMemberReports" />

    </div>

    <div class="team-execution-column team-execution-column--right">
      <article class="team-panel team-focus-panel">
        <div class="team-panel-heading"><div class="team-panel-title"><span class="team-panel-icon team-panel-icon--blue"><UserRound :size="18" /></span><strong>团队重点任务与成果</strong></div><button class="team-more" type="button" @click="openAllReports">查看全部 <ArrowRight :size="14" /></button></div>
        <div class="team-table team-focus-table">
          <div class="team-table-head"><span>成员</span><span>重点任务</span><span>输出成果</span><span>完成进度</span><span>状态</span></div>
          <button v-for="entry in focusTasks" :key="`${entry.member.employee_id}-${entry.task.id}`" class="team-table-row" type="button" @click="openMemberReports(entry.member.employee_id)">
            <span>{{ entry.member.employee_name }}</span><span :title="entry.task.task_name">{{ entry.task.task_name }}</span><span :title="entry.detail?.output_description || '—'">{{ entry.detail?.output_description || "—" }}</span>
            <span class="focus-progress"><i><b :style="{ background: progressColor(entry.task.progress_percent), width: `${Math.min(100, Math.max(0, entry.task.progress_percent))}%` }" /></i><strong :style="{ color: progressColor(entry.task.progress_percent) }">{{ Math.round(entry.task.progress_percent) }}%</strong></span><span class="team-status" :class="entry.task.status === '已完成' ? 'is-done' : 'is-progress'">{{ entry.task.status }}<small v-if="entry.task.detail_count">{{ entry.task.completed_detail_count }}/{{ entry.task.detail_count }}</small></span>
          </button>
          <div v-if="!focusTasks.length" class="team-panel-empty">暂无本周重点任务</div>
        </div>
      </article>

      <article class="team-panel team-plan-panel">
        <div class="team-panel-heading"><div class="team-panel-title"><span class="team-panel-icon team-panel-icon--blue"><Target :size="18" /></span><strong>团队下周计划</strong></div><span class="team-plan-note">明确目标 · 持续突破</span></div>
        <div v-if="plans.length" class="team-plan-timeline">
          <button v-for="(plan, index) in plans" :key="plan.id" class="team-plan-step" type="button" @click="openAllReports">
            <span class="team-plan-node" :class="`team-plan-node--${index % 5}`">{{ String(index + 1).padStart(2, "0") }}</span>
            <span class="team-plan-copy">
              <small>{{ plan.plannedDate || "未设定" }}</small>
              <strong :title="plan.title">{{ plan.title }}</strong>
              <span :title="plan.detail">{{ plan.detail }}</span>
            </span>
          </button>
        </div>
        <div v-else class="team-panel-empty">暂无下周计划</div>
      </article>
    </div>
  </section>
</template>

<style scoped src="./TeamReportsPanel.css"></style>
