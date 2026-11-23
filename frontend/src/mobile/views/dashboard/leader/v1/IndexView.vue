<script setup lang="ts">
import { AlertTriangle } from "lucide-vue-next"
import NoticeBridge from "@/mobile/components/feedback/NoticeBridge.vue"
import LeaderAnalyticsGrid from "./components/LeaderAnalyticsGrid.vue"
import LeaderHomeHeader from "./components/LeaderHomeHeader.vue"
import LeaderMetricGrid from "./components/LeaderMetricGrid.vue"
import LeaderPlansPanel from "./components/LeaderPlansPanel.vue"
import LeaderRelationsPanel from "./components/LeaderRelationsPanel.vue"
import LeaderTaskStatsPanel from "./components/LeaderTaskStatsPanel.vue"
import LeaderWorkGrid from "./components/LeaderWorkGrid.vue"
import { useLeaderDashboard } from "./composables/useLeaderDashboard"
const { authStore, dashboardStore, summary, tasks, nextWeekTasks, currentTasks, workTasks, outputTotal, memberStats, groupStats, roleNameMap, departments, outputDistribution, results, plans, relations, planCoverage, metricCards, formatDate, sectionLabel, splitCollaborators, handlePeriodChange } = useLeaderDashboard()
</script>

<template>
  <div class="leader-home-page">
    <LeaderHomeHeader :period="summary.period" :role-name="roleNameMap[authStore.effectiveRole?.role_code || ''] || authStore.effectiveRole?.role_name || '领导视角'" :user-name="authStore.user?.display_name || ''" @update:start="handlePeriodChange" />
    <NoticeBridge :warning-message="dashboardStore.errorMessage" />

    <div v-if="dashboardStore.isLoading" class="leader-state">正在加载领导首页数据…</div>
    <div v-else-if="dashboardStore.errorMessage" class="leader-state leader-state--error"><AlertTriangle :size="18" />暂无领导首页数据</div>
    <template v-else>
      <LeaderMetricGrid :cards="metricCards" />
      <LeaderAnalyticsGrid :trend="summary.trend" :departments="departments" :output-distribution="outputDistribution" :output-total="outputTotal" :completion-rate="summary.kpis.completion_rate" />
      <LeaderTaskStatsPanel :groups="groupStats" :members="memberStats" :period="summary.period" />
      <LeaderWorkGrid :tasks="workTasks" :results="results" />
      <div class="leader-bottom-grid">
        <LeaderPlansPanel :plans="plans" />
        <LeaderRelationsPanel :relations="relations" />
      </div>
    </template>
  </div>
</template>

<style scoped src="./IndexView.css"></style>
