<script setup lang="ts">
import { useRouter } from "vue-router"
import type { PlanContext } from "@/mobile/features/monthly-plan/types"
defineProps<{ context: PlanContext | null; personal: boolean }>()
const router = useRouter()
function create() { void router.push({name:"mobile-monthly-plan-new",query:{tab:"mine"}}) }
</script>
<template>
  <header class="monthly-list-header">
    <div class="monthly-list-tabs"><slot /></div>
    <button v-if="personal" class="primary-button" type="button" @click="create">新增月度计划</button>
  </header>
</template>
<style scoped src="./MonthlyPlanListHeader.css"></style>
