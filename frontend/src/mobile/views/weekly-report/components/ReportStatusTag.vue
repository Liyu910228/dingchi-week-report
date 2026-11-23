<script setup lang="ts">
import type { ReportStatus } from "@/mobile/features/weekly-report/types"

defineProps<{ status: ReportStatus }>()

const labels: Record<string, string> = {
  not_started: "待开始",
  in_progress: "进行中",
  completed: "已完成",
}
</script>

<template>
  <span :class="['report-status-tag', 'report-status-tag--' + status]">
    {{ labels[status] || status }}
  </span>
</template>

<style scoped src="./ReportStatusTag.css"></style>
