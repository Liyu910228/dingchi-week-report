<script setup lang="ts">
import type { MonthlyPlanTask } from "@/features/weekly-report/monthly-plan/types"
defineProps<{ task: MonthlyPlanTask; readonly?: boolean }>()
const emit = defineEmits<{ patch: [fields: Partial<MonthlyPlanTask>] }>()
</script>
<template>
  <td class="monthly-outcome">
    <span v-if="readonly" class="outcome-text user-content">{{ task.output_description || '—' }}</span>
    <textarea class="user-content" v-else :value="task.output_description || ''" rows="3" maxlength="10000" aria-label="输出成果" placeholder="点击填写输出成果" @change="emit('patch', { output_description: ($event.target as HTMLTextAreaElement).value })" />
  </td>
  <td class="monthly-planned-date">
    <span v-if="readonly" class="user-content">{{ task.planned_date || '—' }}</span>
    <input class="user-content" v-else type="date" :value="task.planned_date || ''" aria-label="计划完成时间" @change="emit('patch', { planned_date: ($event.target as HTMLInputElement).value || null })" />
  </td>
</template>
<style scoped src="./MonthlyPlanOutcomeCells.css"></style>
