<script setup lang="ts">
import type { Component } from "vue"

defineProps<{
  cards: Array<{
    label: string
    value: string | number
    hint: string
    tone: "blue" | "purple" | "green" | "amber" | "red"
    icon: Component
  }>
}>()
</script>

<template>
  <section class="leader-metric-grid" aria-label="领导首页关键指标">
    <article v-for="card in cards" :key="card.label" class="leader-metric-card" :class="`leader-metric-card--${card.tone}`">
      <div class="leader-metric-content">
        <span class="leader-metric-icon" aria-hidden="true"><component :is="card.icon" :size="28" stroke-width="1.9" /></span>
        <div class="leader-metric-copy">
          <span class="leader-metric-label">{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
          <span class="leader-metric-track" aria-hidden="true"><i /></span>
          <span class="leader-metric-hint">{{ card.hint }}</span>
        </div>
      </div>
    </article>
  </section>
</template>

<style scoped src="./LeaderMetricGrid.css"></style>
