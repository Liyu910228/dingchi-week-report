<script setup lang="ts">
import CollapsibleFilters from "@/mobile/components/form/CollapsibleFilters.vue";
import RoleFilterSelect from "@/mobile/features/directory/components/RoleFilterSelect.vue";
defineProps<{
    showMembers: boolean;
    disabled: boolean;
}>();
const month = defineModel<string>("month", { default: "" });
const position = defineModel<string>("position", { default: "" });
const view = defineModel<string>("view", { default: "members" });
const person = defineModel<string>("person", { default: "" });
const emit = defineEmits<{
    search: [];
    reset: [];
}>();
</script>

<template>
  <CollapsibleFilters>
  <form class="report-filter-bar" @submit.prevent="emit('search')">
    <label>所属月度<input v-model="month" type="month" /></label>
    <label>职位<RoleFilterSelect v-model="position" /></label>
    <label v-if="showMembers">查看范围
      <select v-model="view">
        <option value="mine">我的周报</option>
        <option value="members">全部可见周报</option>
      </select>
    </label>
    <label v-if="showMembers && view === 'members'">人员
      <input v-model="person" placeholder="按姓名搜索" maxlength="128" />
    </label>
    <div class="report-filter-actions">
      <button class="primary-button" type="submit" :disabled="disabled">查询</button>
      <button class="ghost-button" type="button" :disabled="disabled" @click="emit('reset')">重置</button>
    </div>
  </form>
  </CollapsibleFilters>
</template>

<style scoped src="./MonthReportFilters.css"></style>
