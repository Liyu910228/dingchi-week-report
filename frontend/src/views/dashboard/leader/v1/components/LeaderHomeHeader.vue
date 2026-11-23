<script setup lang="ts">
import personalProgressMotto from "@/assets/dashboard/personal-progress-motto.png"
import WeekPeriodPicker from "@/components/form/WeekPeriodPicker.vue"

defineProps<{
  period: { start: string; end: string }
  roleName: string
  userName: string
}>()
const emit = defineEmits<{ "update:start": [value: string] }>()
</script>

<template>
  <header class="leader-home-header">
    <div class="leader-header-copy">
      <div class="leader-title-line">
        <span class="leader-title-mark" aria-hidden="true" />
        <div>
          <h1>智能周报 · 领导首页</h1>
          <p class="leader-subtitle">总览经营执行 · 聚焦输出成果 · 统筹下周重点</p>
        </div>
      </div>
    </div>

    <img class="leader-header-art" :src="personalProgressMotto" alt="持续进步，遇见更好的自己！" />

    <div class="leader-header-period">
      <WeekPeriodPicker class="leader-week-button period-main" :start="period.start" :end="period.end" @update:start="emit('update:start', $event)" />
      <div class="leader-period-owner">聚力前行 · 把计划变成成果</div>
    </div>
  </header>
</template>

<style scoped src="./LeaderHomeHeader.css"></style>
