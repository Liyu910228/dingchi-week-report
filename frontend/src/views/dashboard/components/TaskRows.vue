<script setup lang="ts">
import { progressColor } from "@/utils/progress-color"
import type { DashboardItem } from "@/features/dashboard/types"

defineProps<{ tasks: DashboardItem[] }>()

function percent(value: number | null) {
  return value === null ? "—" : `${Math.round(value)}%`
}
</script>

<template>
  <div class="task-rows">
    <div v-if="!tasks.length" class="task-empty">暂无任务数据，请先填写本周周报。</div>
    <div v-else class="task-table-head" aria-hidden="true">
      <span>客户</span>
      <span>工作任务</span>
      <span>进展</span>
      <span>进度</span>
      <span>完成率</span>
      <span>状态</span>
    </div>
    <article v-for="task in tasks" :key="task.id" class="task-row">
      <span class="task-customer">{{ task.customer_name_snapshot || "总体任务" }}</span>
      <div class="task-main">
        <strong>{{ task.task_name_snapshot }}</strong>
        <small>{{ task.progress_text || "尚未填写进展" }}</small>
      </div>
      <div class="task-progress">
        <div class="progress-track"><span :style="{ background: progressColor(task.progress_percent), width: `${task.progress_percent || 0}%` }" /></div>
      </div>
      <span class="task-progress-value" :style="{ color: progressColor(task.progress_percent) }">{{ percent(task.progress_percent) }}</span>
      <span class="task-rate" :style="{ color: progressColor(task.completion_rate) }">{{ percent(task.completion_rate) }}</span>
      <span class="status-pill" :class="`status-pill--${task.on_time_status}`">
        {{ task.on_time_status === "pending" ? "待完成" : task.on_time_status === "overdue" || task.on_time_status === "late" ? "延期" : task.on_time_status === "on_time" || task.on_time_status === "completed" ? "已完成" : "进行中" }}
      </span>
    </article>
  </div>
</template>

<style scoped src="./TaskRows.css"></style>
