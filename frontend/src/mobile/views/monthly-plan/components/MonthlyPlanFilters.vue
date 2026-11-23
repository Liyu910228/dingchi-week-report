<script setup lang="ts">
import CollapsibleFilters from "@/mobile/components/form/CollapsibleFilters.vue"
import { computed, onMounted } from "vue"
import { useDirectoryFilterOptions } from "@/mobile/features/directory/useDirectoryFilterOptions"
import PersonSelect from "@/mobile/features/directory/components/PersonSelect.vue"
import GroupTreeSelect from "@/mobile/features/directory/components/GroupTreeSelect.vue"
import RoleFilterSelect from "@/mobile/features/directory/components/RoleFilterSelect.vue"
import { planStatusLabels, type PlanFilters, type PlanListView } from "@/mobile/features/monthly-plan/types"
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
  <CollapsibleFilters>
  <form class="monthly-filters filter-panel-form" @submit.prevent="emit('search')">
    <p v-if="optionError" role="alert">{{optionError}}</p>
    <label>所属月度<input v-model="filters.month_key" type="month" /></label>
    <label>状态<select v-model="filters.status"><option value="">全部</option><option v-for="status in ['draft','pending','approved','rejected']" :key="status" :value="status">{{planStatusLabels[status]}}</option></select></label>
    <div class="filter-field full-width"><span>职位</span><RoleFilterSelect v-model="role" /></div>
    <div v-if="view !== 'mine'" class="filter-field full-width group-filter"><span>分组</span><GroupTreeSelect :model-value="filters.group_id || null" :groups="groups" empty-label="全部分组" @update:model-value="filters.group_id=$event || ''" /></div>
    <div v-if="view !== 'mine'" class="filter-field full-width"><span>人员</span><PersonSelect v-model="employee" :users="users" /></div>
    <button class="primary-button" type="submit" :disabled="busy">查询</button>
  </form>
  </CollapsibleFilters>
</template>
<style scoped src="./MonthlyPlanFilters.css"></style>

