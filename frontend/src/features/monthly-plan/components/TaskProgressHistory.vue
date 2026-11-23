<script setup lang="ts">
import type { TaskProgressHistoryEntry } from "../types"
import { formatDateTime } from "@/utils/date"
defineProps<{ entries: TaskProgressHistoryEntry[] }>()
const statusLabels: Record<string, string> = { pending: "待完成", in_progress: "进行中", on_time: "按时完成", late: "延期完成", overdue: "逾期未完成", completed: "已完成", not_applicable: "不适用" }
function display(field: string, value: unknown) {
  if (value === null || value === undefined || value === "") return "—"
  if (["progress_percent", "quality_percent", "completion_rate"].includes(field)) return `${value}%`
  if (field === "on_time_status") return statusLabels[String(value)] || String(value)
  return typeof value === "object" ? JSON.stringify(value) : String(value)
}
</script>
<template>
  <section class="dashboard-card progress-history">
    <h2>进度变更历史</h2>
    <p class="progress-history__intro">右侧实时进度独立保存，不改变原计划审批版本。</p>
    <details v-for="entry in entries" :key="entry.id">
      <summary><strong>进度</strong><span class="progress-history__task">{{ entry.task_name }}</span><span>{{ entry.changed_by_name || '本人' }}</span><time :datetime="entry.created_at">{{ formatDateTime(entry.created_at) }}</time></summary>
      <div class="progress-history__changes">
        <div v-for="change in entry.changes" :key="change.field" class="progress-history__change">
          <strong>{{ change.label }}</strong>
          <div><span>修改前</span><p>{{ display(change.field, change.before) }}</p></div>
          <div><span>修改后</span><p>{{ display(change.field, change.after) }}</p></div>
        </div>
        <p v-if="!entry.changes.length">已保存执行进度。</p>
      </div>
    </details>
  </section>
</template>
<style scoped>
.progress-history { padding: 22px; }
.progress-history h2 { margin: 0 0 6px; font-size: 20px; }
.progress-history__intro { margin: 0 0 16px; color: var(--muted); }
.progress-history details { border-top: 1px solid var(--line); }
.progress-history summary { display: grid; grid-template-columns: auto minmax(160px, 1fr) auto auto; gap: 14px; align-items: center; padding: 14px 4px; cursor: pointer; }
.progress-history__task { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.progress-history time, .progress-history__change span { color: var(--muted); font-size: 0.875rem; }
.progress-history__changes { display: grid; gap: 12px; padding: 0 12px 16px; }
.progress-history__change { display: grid; grid-template-columns: minmax(120px, .5fr) 1fr 1fr; gap: 14px; padding: 12px; border-radius: 8px; background: var(--surface-soft); }
.progress-history__change p { margin: 4px 0 0; white-space: pre-wrap; overflow-wrap: anywhere; }
@media (max-width: 720px) { .progress-history summary { grid-template-columns: auto 1fr; } .progress-history__change { grid-template-columns: 1fr; } }
</style>
