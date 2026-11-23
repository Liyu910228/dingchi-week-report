<script setup lang="ts">
import WeekPeriodPicker from "@/mobile/components/form/WeekPeriodPicker.vue"
defineProps<{title:string;period:{start:string;end:string}}>()
defineEmits<{"update:start":[value:string]}>()
</script>
<template>
 <header class="dashboard-overview-header">
  <h1>{{title}}</h1>
  <WeekPeriodPicker class="overview-period" :start="period.start" :end="period.end" @update:start="$emit('update:start',$event)" />
 </header>
</template>
<style scoped src="./DashboardOverviewHeader.css"></style>
