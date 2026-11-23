<script setup lang="ts">
import personalProgressMotto from "@/assets/dashboard/personal-progress-motto.png"
import WeekPeriodPicker from "@/components/form/WeekPeriodPicker.vue"

defineProps<{
  period: { start: string; end: string }
}>()
const emit = defineEmits<{ "update:start": [value: string] }>()
</script>

<template>
  <header class="team-home-header">
    <div class="header-copy">
      <div class="header-title-line">
        <span class="title-mark" aria-hidden="true" />
        <div>
          <h1>智能周报 · 团队首页</h1>
          <p class="header-subtitle">看见团队进展 · 聚焦协同成果 · 驱动下一步行动</p>
        </div>
      </div>
    </div>

    <img class="header-art" :src="personalProgressMotto" alt="持续进步，遇见更好的自己！" />

    <div class="header-period">
      <WeekPeriodPicker class="period-main" :start="period.start" :end="period.end" @update:start="emit('update:start', $event)" />
      <div class="period-owner">
        <span>聚力前行·把计划变成成果</span>
      </div>
    </div>
  </header>
</template>

<style scoped src="./TeamHomeHeader.css"></style>
