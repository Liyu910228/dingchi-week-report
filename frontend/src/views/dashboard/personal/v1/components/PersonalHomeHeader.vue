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
  <header class="personal-home-header">
    <div class="header-copy">
      <div class="header-title-line">
        <span class="title-mark" aria-hidden="true" />
        <div>
          <h1>智能周报 · 个人首页</h1>
          <p class="header-subtitle">聚焦我的进展 · 沉淀工作成果 · 规划下周行动</p>
        </div>
      </div>
    </div>

    <img class="header-motto-art" :src="personalProgressMotto" alt="持续进步，遇见更好的自己！" />

    <div class="header-period">
      <WeekPeriodPicker class="period-main" :start="period.start" :end="period.end" @update:start="emit('update:start', $event)" />
      <div class="period-owner">专注当下 · 积累成长 · 创造更大价值</div>
    </div>
  </header>
</template>

<style scoped src="./PersonalHomeHeader.css"></style>
