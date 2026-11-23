<script setup lang="ts">
import { computed, onMounted } from "vue"
import { useDirectoryFilterOptions } from "@/features/directory/useDirectoryFilterOptions"
import PersonSelect from "@/features/directory/components/PersonSelect.vue"
import GroupTreeSelect from "@/features/directory/components/GroupTreeSelect.vue"
import RoleFilterSelect from "@/features/directory/components/RoleFilterSelect.vue"
import { planStatusLabels, type PlanFilters, type PlanListView } from "@/features/monthly-plan/types"
const filters = defineModel<PlanFilters>({ required: true })
defineProps<{busy: boolean; view: PlanListView}>()
const emit = defineEmits<{search: []}>()
const directory = useDirectoryFilterOptions()
const { users, groups, error: optionError } = directory
const employee = computed({ get:()=>filters.value.employee_id || "", set:(value:string|string[])=>{ filters.value.employee_id=String(value || "") } })
const role = computed({ get:()=>filters.value.role_code || "", set:(value:string)=>{ filters.value.role_code=value } })
onMounted(() => void directory.load())
</script>
<template>
  <form class="monthly-filters" @submit.prevent="emit('search')">
    <p v-if="optionError" role="alert">{{optionError}}</p>
    <label>所属月度<input v-model="filters.month_key" type="month" /></label>
    <label>状态<select v-model="filters.status"><option value="">全部</option><option v-for="status in ['draft','pending','approved','rejected']" :key="status" :value="status">{{planStatusLabels[status]}}</option></select></label>
    <label>职位<RoleFilterSelect v-model="role" /></label>
    <label v-if="view !== 'mine'" class="group-filter">分组<GroupTreeSelect :model-value="filters.group_id || null" :groups="groups" empty-label="全部分组" @update:model-value="filters.group_id=$event || ''" /></label>
    <label v-if="view !== 'mine'">人员<PersonSelect v-model="employee" :users="users" /></label>
    <button class="primary-button" type="submit" :disabled="busy">查询</button>
  </form>
</template>
<style scoped src="./MonthlyPlanFilters.css"></style>
