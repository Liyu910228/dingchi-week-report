<script setup lang="ts">
import { computed } from "vue"
import { Award, ChevronRight, FileText, Star, TrendingUp } from "lucide-vue-next"
import { RouterLink } from "vue-router"

import { isWorkTaskCompleted } from "@/mobile/features/dashboard/task-metrics"
import type { DashboardItem } from "@/mobile/features/dashboard/types"

const props = defineProps<{
  tasks: DashboardItem[]
  reportId: string | null
}>()

const resultItems = computed(() => {
  const completed = props.tasks.filter(isWorkTaskCompleted).length
  const progressing = props.tasks.filter((task) => (task.progress_percent || 0) > 0).length
  const customers = new Set(
    props.tasks
      .map((task) => task.customer_name_snapshot?.trim())
      .filter((name): name is string => Boolean(name)),
  ).size
  return [
    { key: "completed", icon: FileText, prefix: "完成", value: completed, suffix: "项任务", note: "持续高效执行，取得阶段成果" },
    { key: "progressing", icon: TrendingUp, prefix: "推进", value: progressing, suffix: "个工作条目", note: "多项工作稳步推进" },
    { key: "mobile-customers", icon: Star, prefix: "与", value: customers, suffix: "个客户保持良好合作", note: "深化沟通，推动项目进展" },
  ]
})
</script>

<template>
  <article class="personal-content-panel personal-results-panel">
    <div class="content-panel-heading">
      <div class="content-panel-title">
        <span class="content-panel-icon results-title-icon" aria-hidden="true"><Award :size="18" :stroke-width="2.2" /></span>
        <div>
          <h2>本周工作成果</h2>
        </div>
      </div>
      <RouterLink
        v-if="props.reportId"
        class="results-more"
        :to="{ name: 'mobile-weekly-report-detail', params: { reportId: props.reportId } }"
        aria-label="查看全部工作成果"
      >
        <ChevronRight :size="22" />
      </RouterLink>
      <span v-else class="results-more results-more--disabled" aria-hidden="true"><ChevronRight :size="22" /></span>
    </div>

    <div class="result-list">
      <div v-for="item in resultItems" :key="item.key" class="result-item">
        <span class="result-marker" :class="`result-marker--${item.key}`" aria-hidden="true">
          <component :is="item.icon" :size="25" :stroke-width="2.2" />
        </span>
        <div class="result-copy">
          <strong>{{ item.prefix }} <em>{{ item.value }}</em> {{ item.suffix }}</strong>
          <span>{{ item.note }}</span>
        </div>
      </div>
    </div>
  </article>
</template>

<style scoped src="./PersonalResultsPanel.css"></style>
