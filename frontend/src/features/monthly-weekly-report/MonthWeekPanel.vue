<script setup lang="ts">
import { computed } from "vue";
import SubmissionWeeklyReadonly from "@/features/submissions/components/SubmissionWeeklyReadonly.vue";
import type { MonthWeek } from "./types";
const props = defineProps<{
    week: MonthWeek;
    weekNumber: number;
    roleCode: string;
    expanded: boolean;
}>();
const emit = defineEmits<{
    toggle: [
    ];
}>();
const weekLabel = computed(() => `第${["一", "二", "三", "四", "五", "六"][props.weekNumber - 1] || props.weekNumber}周`);
const statusClass = computed(() => props.week.plan.status === "completed" ? "approved" : props.week.plan.status === "in_progress" ? "submitted" : "draft");
const parts = computed(() => props.week.parts.filter(part => part.role_code === props.roleCode));
const labels: Record<string, string> = {
    not_started: "待开始", in_progress: "进行中", completed: "已完成", draft: "草稿",
};
</script>

<template>
  <section class="month-week">
    <button class="month-week-heading" :aria-expanded="expanded" @click="emit('toggle')">
      <span class="month-week-summary">
        <span>{{ weekLabel }}：{{ week.plan.period_start }} 至 {{ week.plan.period_end }}</span>
        <span class="status-pill" :class="`status-pill--${statusClass}`">{{ labels[week.plan.status] || week.plan.status }}</span>
      </span>
      <span class="month-week-toggle">{{ expanded ? '收起' : '展开' }}</span>
    </button>
    <template v-if="expanded">
      <SubmissionWeeklyReadonly v-for="part in parts" :key="part.id" :part="part" />
      <p v-if="!parts.length" class="month-missing">该周未填写此职位的周报。</p>
    </template>
  </section>
</template>

<style scoped src="./MonthWeekPanel.css"></style>
