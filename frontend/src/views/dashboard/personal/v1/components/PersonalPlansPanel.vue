<script setup lang="ts">
import { computed } from "vue"
import { Target } from "lucide-vue-next"
import { RouterLink } from "vue-router"

import planArtwork from "@/assets/dashboard/personal-next-week-plan.png"
import type { DashboardItem } from "@/features/dashboard/types"

const props = defineProps<{
  plans: DashboardItem[]
  period: { start: string; end: string }
}>()

function dayColumn(dateValue: string | null) {
  if (!dateValue || !props.period.start) return 1
  const target = new Date(`${dateValue.slice(0, 10)}T00:00:00`)
  const start = new Date(`${props.period.end.slice(0, 10)}T00:00:00`)
  start.setDate(start.getDate() + 1)
  const day = Math.floor((target.getTime() - start.getTime()) / 86400000)
  return Math.min(7, Math.max(1, day + 1))
}

function dateLabel(value: string | null) {
  return value ? value.slice(0, 10) : "待安排"
}

const timelineDays = computed(() => {
  const end = new Date(`${props.period.end.slice(0, 10)}T00:00:00`)
  const monday = new Date(end)
  monday.setDate(end.getDate() + 1)
  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(monday)
    date.setDate(monday.getDate() + index)
    return {
      week: ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][index],
      date: `${date.getMonth() + 1}/${date.getDate()}`,
    }
  })
})
</script>

<template>
  <article class="personal-content-panel personal-plans-panel">
    <div class="content-panel-heading">
      <div class="content-panel-title">
        <span class="content-panel-icon plans-title-icon" aria-hidden="true"><Target :size="19" :stroke-width="2.35" /></span>
        <div>
          <h2>我的下周计划</h2>
        </div>
        <span class="plans-heading-divider" aria-hidden="true"></span>
        <p class="plans-heading-copy">明确目标，有序安排，为下周的进步做好准备</p>
      </div>
    </div>

    <div v-if="!props.plans.length" class="content-empty">暂无下一步计划</div>
    <div v-else class="plan-board">
      <div class="plan-list">
        <RouterLink
          v-for="(plan, index) in props.plans"
          :key="plan.id"
          class="plan-item"
          :to="{ name: 'weekly-report-detail', params: { reportId: plan.report_id } }"
        >
          <span class="plan-index">{{ String(index + 1).padStart(2, "0") }}</span>
          <div>
            <strong :title="plan.task_name_snapshot">{{ plan.task_name_snapshot }}</strong>
            <small>{{ dateLabel(plan.planned_completion_date) }} · {{ plan.progress_text || "待持续推进" }}</small>
          </div>
        </RouterLink>
      </div>
      <div class="plan-timeline" aria-label="计划排期">
        <div class="timeline-head">
          <span v-for="day in timelineDays" :key="day.week"><b>{{ day.week }}</b><small>{{ day.date }}</small></span>
        </div>
        <div v-for="plan in props.plans" :key="`timeline-${plan.id}`" class="timeline-row">
          <span class="timeline-bar" :style="{ gridColumn: `${dayColumn(plan.planned_completion_date)} / span ${Math.max(1, 7 - dayColumn(plan.planned_completion_date) + 1)}` }" />
        </div>
      </div>
    </div>
    <div class="plan-artwork" aria-hidden="true">
      <img :src="planArtwork" alt="" />
    </div>
  </article>
</template>

<style scoped src="./PersonalPlansPanel.css"></style>
