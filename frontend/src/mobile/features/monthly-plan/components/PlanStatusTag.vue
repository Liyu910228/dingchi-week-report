<script setup lang="ts">
import { planStatusLabels } from "@/mobile/features/monthly-plan/types"
defineProps<{ status: string; label?:string }>()
</script>
<template>
  <span class="plan-status-tag" :class="'plan-status-tag--' + status">{{label || planStatusLabels[status] || status}}</span>
</template>
<style scoped src="./PlanStatusTag.css"></style>
