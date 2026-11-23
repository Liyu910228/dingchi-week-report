<script setup lang="ts">
import { progressColor } from "@/mobile/utils/progress-color"
import { ArrowUpRight, BarChart3, CalendarCheck2, ClipboardCheck, ListChecks, PieChart, Target, UsersRound } from "lucide-vue-next"
import { useRouter } from "vue-router"

import type { DashboardDistribution, DashboardTrendPoint } from "@/mobile/features/dashboard/types"

import TeamStatusChart from "./TeamStatusChart.vue"
import TeamTrendChart from "./TeamTrendChart.vue"
import type { TeamMemberSummary, TeamReportEntry } from "../types"

const props = defineProps<{
  trend: DashboardTrendPoint[]
  statusDistribution: DashboardDistribution[]
  taskTotal: number
  members: TeamMemberSummary[]
  myReport: TeamReportEntry | null
  ownTaskCount: number
  ownPlanCount: number
}>()

const router = useRouter()

function openMyReport() {
  if (!props.myReport?.id) return
  void router.push({ name: "mobile-weekly-report-detail", params: { reportId: props.myReport.id } })
}
</script>

<template>
  <section class="team-analytics-grid">
    <article class="team-panel team-own-panel">
      <div class="team-panel-heading">
        <div class="team-panel-title">
          <span class="team-panel-icon team-panel-icon--blue"><ClipboardCheck :size="16" stroke-width="2" /></span>
          <div><strong>我的周报</strong></div>
        </div>
        <button v-if="myReport" class="own-report-link" type="button" @click="openMyReport">查看详情 <ArrowUpRight :size="13" /></button>
      </div>
      <div class="own-report-stats">
        <button class="own-report-stat own-report-stat--blue" type="button" :disabled="!myReport" @click="openMyReport">
          <span><Target :size="18" /></span><div><strong :style="{ color: progressColor(myReport?.completionRate || 0) }">{{ Math.round(myReport?.completionRate || 0) }}%</strong><small>个人完成率</small></div>
        </button>
        <button class="own-report-stat own-report-stat--purple" type="button" :disabled="!myReport" @click="openMyReport">
          <span><ListChecks :size="18" /></span><div><strong>{{ ownTaskCount }}</strong><small>本周条目</small></div>
        </button>
        <button class="own-report-stat own-report-stat--green" type="button" :disabled="!myReport" @click="openMyReport">
          <span><CalendarCheck2 :size="18" /></span><div><strong>{{ ownPlanCount }}</strong><small>下周计划</small></div>
        </button>
      </div>
    </article>

    <article class="team-panel team-trend-panel">
      <div class="team-panel-heading">
        <div class="team-panel-title">
          <span class="team-panel-icon team-panel-icon--blue"><BarChart3 :size="16" stroke-width="2" /></span>
          <div><strong>本周完成进展</strong></div>
        </div>
        <div v-if="trend.length" class="team-trend-legend" aria-label="趋势图例">
          <span class="team-legend-blue">进展</span>
          <span class="team-legend-green">完成率</span>
        </div>
      </div>
      <TeamTrendChart :points="trend" />
    </article>

    <article class="team-panel team-member-panel">
      <div class="team-panel-heading">
        <div class="team-panel-title">
          <span class="team-panel-icon team-panel-icon--purple"><UsersRound :size="16" stroke-width="2" /></span>
          <div><strong>成员完成排行</strong></div>
        </div>
      </div>
      <div v-if="members.length" class="member-progress-list">
        <div v-for="member in members.slice(0, 5)" :key="member.employeeId" class="member-progress-item">
          <div class="member-progress-name">
            <span class="member-avatar">{{ member.employeeName.slice(0, 1) }}</span>
            <div><strong>{{ member.employeeName }}</strong><small>{{ member.roleName }} · {{ member.taskCount }} 项任务，完成 {{ member.completedTaskCount }} 项</small></div>
            <b :style="{ color: progressColor(member.completionRate) }">{{ Math.round(member.completionRate) }}%</b>
          </div>
          <div class="member-progress-track"><i :style="{ background: progressColor(member.completionRate), width: `${Math.min(100, Math.max(0, member.completionRate))}%` }" /></div>
        </div>
      </div>
      <div v-else class="team-panel-empty">暂无团队任务</div>
    </article>

    <article class="team-panel team-status-panel">
      <div class="team-panel-heading">
        <div class="team-panel-title">
          <span class="team-panel-icon team-panel-icon--green"><PieChart :size="16" stroke-width="2" /></span>
          <div><strong>状态分布</strong></div>
        </div>
      </div>
      <div class="status-panel-body">
        <TeamStatusChart :data="statusDistribution" :total="taskTotal" />
        <div class="status-legend">
          <div v-for="item in statusDistribution" :key="item.name" class="status-legend-item">
            <i :style="{ background: item.color }" /><span>{{ item.name }}</span><strong>{{ item.value }}</strong>
          </div>
          <span v-if="!statusDistribution.length" class="team-panel-empty">暂无状态数据</span>
        </div>
      </div>
    </article>
  </section>
</template>

<style scoped src="./TeamAnalyticsGrid.css"></style>
