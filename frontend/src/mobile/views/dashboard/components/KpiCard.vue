<script setup lang="ts">
import kpiSprite from "@/assets/dashboard/dashboard-kpi-sprite.png"

defineProps<{
  label: string
  value: string | number
  hint: string
  tone: "blue" | "purple" | "green" | "red"
  icon: "clipboard" | "target" | "check" | "alert"
}>()
</script>

<template>
  <article class="kpi-card" :class="`kpi-card--${tone}`">
    <span
      class="kpi-icon"
      :class="`kpi-icon--${icon}`"
      :style="{ backgroundImage: `url(${kpiSprite})` }"
      aria-hidden="true"
    />
    <div>
      <p>{{ label }}</p>
      <strong>{{ value }}</strong>
      <span>{{ hint }}</span>
    </div>
  </article>
</template>

<style scoped src="./KpiCard.css"></style>
