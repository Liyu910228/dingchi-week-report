<script setup lang="ts">
import { CalendarDays, Target } from "lucide-vue-next"

import type { LeaderPlan } from "../types"

const props = defineProps<{ plans: LeaderPlan[] }>()
</script>

<template>
  <article class="leader-plans-panel">
    <div class="leader-bottom-heading"><div class="leader-bottom-title"><span class="leader-bottom-icon leader-bottom-icon--blue"><CalendarDays :size="17" /></span><h2>下周重点计划</h2></div></div>
    <div v-if="!props.plans.length" class="leader-bottom-empty">暂无下周计划</div>
    <div v-else class="leader-plan-list">
      <div v-for="(plan, index) in props.plans.slice(0, 3)" :key="plan.id" class="leader-plan-item">
        <span class="leader-plan-index">{{ String(index + 1).padStart(2, "0") }}</span>
        <div class="leader-plan-body"><strong :title="plan.name">{{ plan.name }}</strong><span :title="plan.note">{{ plan.note }}</span></div>
        <div class="leader-plan-meta"><small>{{ plan.owner || "未指定" }}</small><b>{{ plan.date }}</b></div>
      </div>
    </div>
    <div v-if="props.plans.length" class="leader-plan-foot"><Target :size="14" /> 计划执行情况将同步到下一周期周报</div>
  </article>
</template>

<style scoped src="./LeaderPlansPanel.css"></style>
