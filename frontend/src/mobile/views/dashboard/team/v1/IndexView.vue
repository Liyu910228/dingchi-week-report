<script setup lang="ts">
import { AlertTriangle } from "lucide-vue-next"
import NoticeBridge from "@/mobile/components/feedback/NoticeBridge.vue"
import TeamAnalyticsGrid from "./components/TeamAnalyticsGrid.vue"
import TeamHomeHeader from "./components/TeamHomeHeader.vue"
import TeamMetricGrid from "./components/TeamMetricGrid.vue"
import TeamReportsPanel from "./components/TeamReportsPanel.vue"
import { useTeamDashboard } from "./composables/useTeamDashboard"
const { authStore, dashboardStore, summary, roleNameMap, reports, submissionReports, teamTasks, nextWeekTasks, memberStats, currentReports, currentTasks, members, myReport, plans, currentReportTotal, currentTaskTotal, currentCompletedTaskTotal, currentRiskTaskTotal, currentCollaborationTotal, ownTaskCount, ownPlanCount, currentCompletionRate, currentStatusDistribution, metricCards, handlePeriodChange, formatDate, parseDate, taskCompletionRate, isTaskCompleted, isTaskRisk, taskRiskText, taskStatusText } = useTeamDashboard()
</script>

<template>
  <div class="team-home-page">
    <TeamHomeHeader :period="summary.period" @update:start="handlePeriodChange" />
    <NoticeBridge :warning-message="dashboardStore.errorMessage" />

    <div v-if="dashboardStore.isLoading" class="team-state">正在加载团队数据…</div>
    <div v-else-if="dashboardStore.errorMessage" class="team-state team-state--error">
      <AlertTriangle :size="18" />暂无团队首页数据
    </div>
    <template v-else>
      <TeamMetricGrid :cards="metricCards" />
      <TeamAnalyticsGrid
        :trend="summary.trend"
        :status-distribution="currentStatusDistribution"
        :task-total="currentTaskTotal"
        :members="members"
        :my-report="myReport"
        :own-task-count="ownTaskCount"
        :own-plan-count="ownPlanCount"
      />
      <TeamReportsPanel
        :reports="submissionReports"
        :members="members"
        :member-stats="memberStats"
        :tasks="currentTasks"
        :plans="plans"
        :period="summary.period"
      />
    </template>
  </div>
</template>

<style scoped src="./IndexView.css"></style>
