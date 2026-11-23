<script setup lang="ts">
import type { RoleGoalSummary } from "@/mobile/features/monthly-plan/types"
defineProps<{ summary: string; sections?: RoleGoalSummary[] }>()
</script>
<template>
 <div v-if="sections && sections.length > 1" class="goal-summaries">
  <section v-for="section in sections" :key="section.role_code" class="goal-summary-section" :aria-label="section.role_name">
   <h3>{{ section.role_name || section.role_code }}</h3>
   <p class="user-content">{{ section.summary || '—' }}</p>
  </section>
 </div>
 <p v-else class="goal-summary-text user-content">{{ sections?.[0]?.summary || summary || '—' }}</p>
</template>
<style scoped src="./MonthlyGoalSummary.css"></style>
