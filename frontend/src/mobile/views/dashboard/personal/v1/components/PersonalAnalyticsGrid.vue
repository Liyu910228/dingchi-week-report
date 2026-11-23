<script setup lang="ts">
import { computed } from "vue"
import { BarChart3, CheckCircle2, CircleGauge, Users, Activity } from "lucide-vue-next"

import type { DashboardDistribution, DashboardTrendPoint } from "@/mobile/features/dashboard/types"
import overallArtwork from "@/assets/dashboard/personal-overall-completion-bg.png"

import PersonalDonutChart from "./PersonalDonutChart.vue"
import PersonalGaugeChart from "./PersonalGaugeChart.vue"
import PersonalTrendChart from "./PersonalTrendChart.vue"

const props = defineProps<{
  plannedTasks: number
  trend: DashboardTrendPoint[]
  statusDistribution: DashboardDistribution[]
  customerDistribution: DashboardDistribution[]
  completionRate: number
}>()

function sum(data: DashboardDistribution[]) {
  return data.reduce((total, item) => total + item.value, 0)
}

function distributionLabel(name: string) {
  return name === "in_progress" ? "进行中" : name === "on_time" ? "已完成" : name === "overdue" || name === "late" ? "延期/风险" : name
}

const statusTotal = computed(() => sum(props.statusDistribution))
const customerTotal = computed(() => sum(props.customerDistribution))
const hasStatusData = computed(() => statusTotal.value > 0)
const hasCustomerData = computed(() => customerTotal.value > 0)
const hasTrendData = computed(() =>
  props.trend.length > 0 && (props.plannedTasks > 0 || props.trend.some((point) => point.progress > 0 || point.completion > 0)),
)
const hasOverallData = computed(() => props.plannedTasks > 0 || hasStatusData.value || hasCustomerData.value || props.completionRate > 0)
</script>

<template>
  <section class="personal-analytics-grid">
    <article class="personal-panel personal-trend-panel">
      <div class="personal-panel-heading">
        <div class="panel-title">
          <span class="panel-icon panel-icon--blue" aria-hidden="true"><BarChart3 :size="17" /></span>
          <div>
            <h2>我的本周进展</h2>
          </div>
        </div>
        <div v-if="hasTrendData" class="chart-legend"><span class="legend-blue">进展</span><span class="legend-green">完成率</span></div>
      </div>
      <PersonalTrendChart v-if="hasTrendData" :points="props.trend" />
      <div v-else class="analytics-empty analytics-empty--trend">暂无进展数据</div>
    </article>

    <article class="personal-panel personal-distribution-panel">
      <div class="personal-panel-heading">
        <div class="panel-title">
          <span class="panel-icon panel-icon--purple" aria-hidden="true"><Activity :size="16" /></span>
          <div>
            <h2>任务状态分布</h2>
          </div>
        </div>
      </div>
      <div v-if="hasStatusData" class="distribution-content">
        <div class="distribution-chart-wrap">
          <PersonalDonutChart :data="props.statusDistribution" />
          <strong>{{ statusTotal }}</strong>
          <span>总任务</span>
        </div>
        <div class="distribution-legend">
          <div v-for="item in props.statusDistribution" :key="item.name" class="distribution-legend-item">
            <span class="legend-dot" :style="{ backgroundColor: item.color }" />
            <span :title="distributionLabel(item.name)">{{ distributionLabel(item.name) }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </div>
      <div v-else class="analytics-empty">暂无任务状态数据</div>
    </article>

    <article class="personal-panel personal-distribution-panel">
      <div class="personal-panel-heading">
        <div class="panel-title">
          <span class="panel-icon panel-icon--green" aria-hidden="true"><Users :size="16" /></span>
          <div>
            <h2>客户任务占比</h2>
          </div>
        </div>
      </div>
      <div v-if="hasCustomerData" class="distribution-content">
        <div class="distribution-chart-wrap">
          <PersonalDonutChart :data="props.customerDistribution" />
          <strong>{{ customerTotal }}</strong>
          <span>总任务</span>
        </div>
        <div class="distribution-legend">
          <div v-for="item in props.customerDistribution.slice(0, 3)" :key="item.name" class="distribution-legend-item">
            <span class="legend-dot" :style="{ backgroundColor: item.color }" />
            <span class="legend-text" :title="item.name">{{ item.name }}</span>
            <strong>{{ item.value }}</strong>
          </div>
        </div>
      </div>
      <div v-else class="analytics-empty">暂无客户任务</div>
    </article>

    <article class="personal-panel personal-overall-panel">
      <img class="overall-artwork" :src="overallArtwork" alt="" aria-hidden="true" />
      <div class="personal-panel-heading">
        <div class="panel-title">
          <span class="panel-icon panel-icon--cyan" aria-hidden="true"><CircleGauge :size="17" /></span>
          <div>
            <h2>整体完成率</h2>
          </div>
        </div>
      </div>
      <div v-if="hasOverallData" class="overall-content">
        <PersonalGaugeChart :value="props.completionRate" />
        <div class="overall-note"><CheckCircle2 :size="16" aria-hidden="true" /><span>本周整体完成情况良好</span></div>
      </div>
      <div v-else class="analytics-empty">暂无完成率数据</div>
    </article>
  </section>
</template>

<style scoped src="./PersonalAnalyticsGrid.css"></style>
