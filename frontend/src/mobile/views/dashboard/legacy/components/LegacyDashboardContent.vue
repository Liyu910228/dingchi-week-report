<script setup lang="ts">
import { progressColor } from "@/mobile/utils/progress-color"
import { toRefs, type UnwrapRef } from "vue"
import type { useLegacyDashboard } from "../composables/useLegacyDashboard"
import heroActionChecklist from "@/assets/dashboard/hero-action-checklist.png"
import heroDataColumns from "@/assets/dashboard/hero-data-columns.png"
import heroProgressArrow from "@/assets/dashboard/hero-progress-arrow.png"
import NoticeBridge from "@/mobile/components/feedback/NoticeBridge.vue"
import DonutChart from "@/mobile/views/dashboard/components/DonutChart.vue"
import KpiCard from "@/mobile/views/dashboard/components/KpiCard.vue"
import TaskRows from "@/mobile/views/dashboard/components/TaskRows.vue"
import TrendChart from "@/mobile/views/dashboard/components/TrendChart.vue"
const props = defineProps<{ state: UnwrapRef<ReturnType<typeof useLegacyDashboard>> }>()
const { authStore, dashboardStore, summary, workTasks, scopeLabel, customerDistribution, customerChartData, nextPlans, weekDays, formatPeriod, riskLabel } = toRefs(props.state)
</script>

<template>
  <div class="dashboard-page">
    <section class="dashboard-hero">
      <div class="hero-copy">
        <h1>智能周报驾驶舱</h1>
        <p>聚焦本周进展 · 洞察风险 · 驱动下周行动</p>
      </div>
      <div class="hero-slogan">让每一周 · 更进一步！</div>
      <img class="hero-data-art" :src="heroDataColumns" alt="" aria-hidden="true" />
      <div class="hero-period">
        <span>本周周期</span>
        <strong>{{ formatPeriod(summary.period.start) }} - {{ formatPeriod(summary.period.end) }}</strong>
        <small>{{ scopeLabel }} · {{ authStore.effectiveRole?.role_name || "周报成员" }}</small>
      </div>
    </section>

    <NoticeBridge :warning-message="dashboardStore.errorMessage" />

    <section class="kpi-grid" aria-label="周报关键指标">
      <KpiCard label="本周条目" :value="summary.kpis.planned_tasks" hint="计划任务总数" tone="blue" icon="clipboard" />
      <KpiCard label="个人完成率" :value="`${Math.round(summary.kpis.completion_rate)}%`" hint="进度与质量综合" tone="purple" icon="target" />
      <KpiCard label="已完成任务" :value="summary.kpis.completed_tasks" hint="按时完成" tone="green" icon="check" />
      <KpiCard label="延期 / 风险项" :value="summary.kpis.risk_items" hint="需要持续关注" tone="red" icon="alert" />
    </section>

    <section class="chart-grid">
      <article class="dashboard-card trend-card">
        <div class="section-heading">
          <div class="section-title">
            <span class="section-icon section-icon--chart" aria-hidden="true" />
            <h2>本周进展趋势</h2>
          </div>
          <span class="section-note">进展&nbsp;&nbsp; 完成率</span>
        </div>
        <TrendChart :points="summary.trend" />
      </article>

      <article class="dashboard-card distribution-card">
        <div class="section-heading">
          <div class="section-title">
            <span class="section-icon section-icon--status" aria-hidden="true" />
            <h2>任务状态分布</h2>
          </div>
        </div>
        <div class="distribution-body">
          <div class="donut-wrap">
            <DonutChart :data="summary.status_distribution" />
            <strong>{{ summary.kpis.planned_tasks }}</strong>
            <span>总任务</span>
          </div>
          <div class="legend-list">
            <div v-for="item in summary.status_distribution" :key="item.name" class="legend-item">
              <span class="legend-dot" :style="{ background: item.color }" />
              <span>{{ item.name }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
        </div>
      </article>

      <article class="dashboard-card distribution-card customer-card">
        <div class="section-heading">
          <div class="section-title">
            <span class="section-icon section-icon--customer" aria-hidden="true" />
            <h2>客户任务占比</h2>
          </div>
        </div>
        <div class="distribution-body">
          <div class="donut-wrap">
            <DonutChart :data="customerChartData" />
            <strong>{{ summary.my_tasks.length }}</strong>
            <span>总任务</span>
          </div>
          <div class="legend-list">
            <div v-for="item in customerDistribution.slice(0, 3)" :key="item.name" class="legend-item">
              <span class="legend-dot" :style="{ background: item.color }" />
              <span>{{ item.name }}</span>
              <strong>{{ item.value }}</strong>
            </div>
            <span v-if="!customerDistribution.length" class="legend-empty">暂无客户任务</span>
          </div>
        </div>
      </article>

      <article class="dashboard-card completion-card">
        <div class="section-heading">
          <div class="section-title">
            <span class="section-icon section-icon--complete" aria-hidden="true" />
            <h2>整体完成率</h2>
          </div>
        </div>
        <div class="completion-visual">
          <img class="completion-art" :src="heroProgressArrow" alt="" aria-hidden="true" />
          <div class="completion-ring" :style="{ '--completion': `${summary.kpis.completion_rate}%` }">
            <div><strong :style="{ color: progressColor(summary.kpis.completion_rate) }">{{ Math.round(summary.kpis.completion_rate) }}%</strong><span>综合完成</span></div>
          </div>
        </div>
        <p class="completion-note">本周整体完成情况良好</p>
      </article>
    </section>

    <section class="dashboard-lower-grid">
      <article class="dashboard-card tasks-card">
        <div class="section-heading section-heading--wide">
          <div class="section-title">
            <span class="section-icon section-icon--target" aria-hidden="true" />
            <h2>我的本周条目</h2>
            <span class="section-subtitle">聚焦关键任务，推动问题解决</span>
          </div>
          <RouterLink class="ghost-button" to="/mobile/weekly-reports">查看全部</RouterLink>
        </div>
        <TaskRows :tasks="summary.my_work_tasks ?? summary.my_tasks" />
      </article>

      <article class="dashboard-card risk-card">
        <div class="section-heading">
          <div class="section-title">
            <span class="section-icon section-icon--risk" aria-hidden="true" />
            <h2>风险概览</h2>
          </div>
          <span class="risk-total">{{ summary.kpis.risk_items }}</span>
        </div>
        <div class="risk-metrics">
          <div class="risk-metric risk-metric--red"><strong>{{ summary.kpis.risk_items }}</strong><span>延期 / 风险项</span></div>
          <div class="risk-metric risk-metric--blue"><strong>0</strong><span>本周新增风险</span></div>
          <div class="risk-metric risk-metric--green"><strong>0</strong><span>已解决风险</span></div>
        </div>
        <div v-if="summary.reports.length" class="risk-list">
          <div v-for="report in summary.reports.slice(0, 2)" :key="report.id" class="risk-list-item">
            <span :class="`risk-mark risk-mark--${report.risk_level}`" />
            <div><strong>{{ report.employee_name }}</strong><small>{{ riskLabel(report.risk_level) }} · {{ report.summary || "暂无摘要" }}</small></div>
          </div>
        </div>
        <p v-else class="risk-empty">暂无新的高风险上报，继续保持。</p>
      </article>
    </section>

    <section class="dashboard-card next-card">
      <div class="section-heading section-heading--wide">
        <div class="section-title">
          <span class="section-icon section-icon--plan" aria-hidden="true" />
          <h2>我的下周计划</h2>
          <span class="section-subtitle">提前规划，聚焦重点，保障目标达成</span>
        </div>
      </div>

      <div v-if="nextPlans.length" class="next-plan-board">
        <div class="next-plan-list">
          <div v-for="(task, index) in nextPlans" :key="`next-${task.id}`" class="next-plan-copy">
            <span class="plan-index">0{{ index + 1 }}</span>
            <div>
              <strong>{{ task.task_name_snapshot }}</strong>
              <small>已进入计划池，主管可一键转办</small>
            </div>
          </div>
        </div>

        <div class="next-timeline" aria-label="下周计划排期">
          <div class="timeline-header">
            <span v-for="day in weekDays" :key="day">{{ day }}</span>
          </div>
          <div v-for="(task, index) in nextPlans" :key="`timeline-${task.id}`" class="timeline-row">
            <span
              class="timeline-bar"
              :class="`timeline-bar--${index + 1}`"
              :style="{ gridColumn: index === 0 ? '1 / span 4' : '3 / span 3' }"
            >
              <i />
            </span>
          </div>
        </div>

        <div class="next-illustration" aria-hidden="true">
          <img :src="heroActionChecklist" alt="" />
          <span>下周 · 落地执行<br />让结果发生！</span>
        </div>
      </div>
      <div v-else class="next-empty">创建本周周报后，系统会自动生成下周行动卡片。</div>
    </section>
  </div>
</template>

<style scoped src="./LegacyDashboardContent.css"></style>

