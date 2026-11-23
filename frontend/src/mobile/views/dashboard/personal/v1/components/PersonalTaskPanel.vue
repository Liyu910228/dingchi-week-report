<script setup lang="ts">
import { progressColor } from "@/mobile/utils/progress-color"
import { computed } from "vue"
import { ListTodo, ArrowUpRight } from "lucide-vue-next"
import { RouterLink } from "vue-router"

import { taskCompletionText } from "@/mobile/features/dashboard/task-metrics"
import type { DashboardItem } from "@/mobile/features/dashboard/types"

const props = defineProps<{
  tasks: DashboardItem[]
  reportId: string | null
}>()

const sortedTasks = computed(() => {
  return [...props.tasks].sort((left, right) => {
    const leftDate = left.planned_completion_date?.slice(0, 10) || "9999-12-31"
    const rightDate = right.planned_completion_date?.slice(0, 10) || "9999-12-31"
    return leftDate.localeCompare(rightDate)
  }).slice(0, 8)
})

function percent(value: number | null) {
  return value === null ? "—" : `${Math.round(value)}%`
}

function statusLabel(status: string) {
  if (status === "pending") return "待完成"
  if (status === "overdue" || status === "late") return "延期"
  return status === "on_time" || status === "completed" ? "已完成" : "进行中"
}
</script>

<template>
  <article class="personal-content-panel personal-task-panel">
    <div class="content-panel-heading">
      <div class="content-panel-title">
        <span class="content-panel-icon task-title-icon" aria-hidden="true"><ListTodo :size="18" :stroke-width="2.25" /></span>
        <div>
          <h2>我的本周条目</h2>
        </div>
        <span class="task-heading-divider" aria-hidden="true"></span>
        <p class="task-heading-copy">聚焦执行，记录成果，让每一份努力都有迹可循</p>
      </div>
      <RouterLink
        v-if="props.reportId"
        class="panel-link"
        :to="{ name: 'mobile-weekly-report-detail', params: { reportId: props.reportId } }"
      >
        查看全部 <ArrowUpRight :size="14" aria-hidden="true" />
      </RouterLink>
      <span v-else class="panel-link panel-link--disabled" aria-disabled="true">
        查看全部 <ArrowUpRight :size="14" aria-hidden="true" />
      </span>
    </div>

    <div v-if="!tasks.length" class="content-empty">暂无任务数据</div>
    <div v-else class="personal-task-table">
      <div class="personal-task-table-head" aria-hidden="true">
        <span>客户</span><span>工作任务</span><span>进展</span><span>进度</span><span>完成情况</span><span>状态</span>
      </div>
      <div v-for="task in sortedTasks" :key="task.id" class="personal-task-row">
        <span class="task-customer" :title="task.customer_name_snapshot || '内部事项'">{{ task.customer_name_snapshot || "内部事项" }}</span>
        <div class="task-name" :title="task.task_name_snapshot">
          <strong>{{ task.task_name_snapshot }}</strong>
        </div>
        <div class="task-progress-track" aria-hidden="true"><span :style="{ background: progressColor(task.progress_percent), width: `${task.progress_percent || 0}%` }" /></div>
        <span class="task-number">{{ percent(task.progress_percent) }}</span>
        <span class="task-number task-number--green">{{ taskCompletionText(task) }}</span>
        <span class="task-status" :class="`task-status--${task.on_time_status}`">{{ statusLabel(task.on_time_status) }}</span>
      </div>
    </div>
  </article>
</template>

<style scoped src="./PersonalTaskPanel.css"></style>
