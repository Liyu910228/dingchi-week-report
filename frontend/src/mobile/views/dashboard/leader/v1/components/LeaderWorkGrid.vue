<script setup lang="ts">
import { progressColor } from "@/mobile/utils/progress-color"
import { BarChart3, CheckCircle2, FileText, ListChecks, Settings, Star } from "lucide-vue-next"

import { isWorkTaskCompleted, taskCompletionText } from "@/mobile/features/dashboard/task-metrics"
import type { DashboardTeamTask } from "@/mobile/features/dashboard/types"

import type { LeaderResult } from "../types"

const props = defineProps<{ tasks: DashboardTeamTask[]; results: LeaderResult[] }>()

function formatDate(value: string | null | undefined) {
  return value ? value.slice(0, 10) : "—"
}

function formatProgress(value: number | string | null | undefined) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? `${Math.round(parsed)}%` : "0%"
}

function taskState(task: DashboardTeamTask) {
  return isWorkTaskCompleted(task) ? "已完成" : task.on_time_status === "overdue" ? "延期/风险" : "进行中"
}
</script>

<template>
  <section class="leader-work-grid">
    <article class="leader-work-panel">
      <div class="leader-work-heading">
        <div class="leader-section-title"><span class="leader-section-icon leader-section-icon--blue"><ListChecks :size="17" /></span><h2>重点工作总览</h2></div>
        <span class="leader-section-count">{{ props.tasks.length }} 项任务</span>
      </div>
      <div class="leader-task-table-wrap">
        <table class="leader-task-table">
          <thead><tr><th>序号</th><th>工作任务</th><th>主要工作内容</th><th>输出成果</th><th>计划完成时间</th><th>工作进度</th><th>完成进度</th><th>计划执行情况</th><th>责任人</th><th>协作人</th></tr></thead>
          <tbody>
            <tr v-for="(task, index) in props.tasks.slice(0, 3)" :key="task.id">
              <td>{{ index + 1 }}</td>
              <td class="leader-task-table__strong" :title="task.task_name_snapshot || undefined">{{ task.task_name_snapshot || "未命名任务" }}</td>
              <td :title="task.work_content || undefined">{{ task.work_content || "—" }}</td>
              <td :title="task.output_description || undefined">{{ task.output_description || "—" }}</td>
              <td>{{ formatDate(task.planned_completion_date) }}</td>
              <td :title="task.progress_text || undefined">{{ task.progress_text || "—" }}</td>
              <td><span class="leader-progress"><i :style="{ background: progressColor(task.progress_percent), width: `${Math.min(100, Math.max(0, Number(task.progress_percent) || 0))}%` }" /><b>{{ formatProgress(task.progress_percent) }}</b></span></td>
              <td><span class="leader-status" :class="`leader-status--${taskState(task) === '进行中' ? 'progress' : taskState(task) === '已完成' ? 'done' : 'pending'}`">{{ taskState(task) }}</span><small v-if="task.detail_count" class="task-completion-count">{{ taskCompletionText(task) }}</small></td>
              <td>{{ task.employee_name || "—" }}</td>
              <td :title="task.collaborator_names || undefined">{{ task.collaborator_names || "—" }}</td>
            </tr>
            <tr v-if="!props.tasks.length"><td colspan="10" class="leader-task-table__empty">暂无重点工作</td></tr>
          </tbody>
        </table>
      </div>
      <div v-if="props.tasks.length > 3" class="leader-work-foot">展示前 3 项任务，其余可在周报列表中查看</div>
    </article>

    <article class="leader-result-panel">
      <div class="leader-work-heading">
        <div class="leader-section-title"><span class="leader-section-icon leader-section-icon--purple"><Star :size="17" /></span><h2>本周重点成果</h2></div>
        <BarChart3 :size="18" class="leader-heading-muted" />
      </div>
      <div v-if="!props.results.length" class="leader-result-empty"><FileText :size="22" /><span>暂无成果记录</span></div>
      <div v-else class="leader-result-list">
        <div v-for="(result, index) in props.results.slice(0, 3)" :key="result.id" class="leader-result-card">
          <span class="leader-result-card__icon">
            <CheckCircle2 v-if="index === 0" :size="22" />
            <BarChart3 v-else-if="index === 1" :size="22" />
            <Settings v-else :size="22" />
          </span>
          <div class="leader-result-card__body"><strong :title="result.name">{{ result.name }}</strong><span>{{ result.category }} · {{ result.owner || "未填写负责人" }}</span><small :title="result.file">{{ result.file }}</small></div>
        </div>
      </div>
    </article>
  </section>
</template>

<style scoped src="./LeaderWorkGrid.css"></style>
