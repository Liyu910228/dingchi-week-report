<script setup lang="ts">
import { ref } from "vue"

import RoleFilterSelect from "@/features/directory/components/RoleFilterSelect.vue"
import PersonSelect from "@/features/directory/components/PersonSelect.vue"
import GroupTreeSelect from "@/features/directory/components/GroupTreeSelect.vue"
import type { DirectoryGroup, DirectoryUserOption } from "@/features/directory/types"

withDefaults(
  defineProps<{
    monthKey: string
    periodStart: string
    periodEnd: string
    roleCode?: string
    groupId?: string
    groupOptions?: DirectoryGroup[]
    showGroup?: boolean
    showPerson?: boolean
    employeeName?: string
    showName?: boolean
    employeeId?: string
    userOptions?: DirectoryUserOption[]
  }>(),
  { roleCode: "", groupId: "", groupOptions: () => [], showGroup: false, showPerson:false, employeeId:"",userOptions:()=>[] },
)

const emit = defineEmits<{
  "update:monthKey": [value: string]
  "update:periodStart": [value: string]
  "update:periodEnd": [value: string]
  "update:roleCode": [value: string]
  "update:groupId": [value: string]
  "update:employeeName": [value:string]
  "update:employeeId": [value:string]
  search: []
  reset: []
}>()
const periodInput = ref<HTMLInputElement | null>(null)

function openPeriodPicker() {
  const input = periodInput.value
  if (!input) return
  const picker = input as HTMLInputElement & { showPicker?: () => void }
  if (picker.showPicker) {
    picker.showPicker()
  } else {
    input.focus()
    input.click()
  }
}

function toLocalDate(value: string) {
  return new Date(value + "T00:00:00")
}

function formatDate(value: Date) {
  const month = String(value.getMonth() + 1).padStart(2, "0")
  const day = String(value.getDate()).padStart(2, "0")
  return `${value.getFullYear()}-${month}-${day}`
}

function mondayOf(value: string) {
  const date = toLocalDate(value)
  const day = date.getDay() || 7
  date.setDate(date.getDate() - day + 1)
  return formatDate(date)
}

function sundayOf(value: string) {
  const date = toLocalDate(value)
  date.setDate(date.getDate() + 6)
  return formatDate(date)
}

function updatePeriodStart(value: string) {
  if (!value) {
    emit("update:periodStart", "")
    emit("update:periodEnd", "")
    return
  }
  const start = mondayOf(value)
  emit("update:periodStart", start)
  emit("update:periodEnd", sundayOf(start))
}
</script>

<template>
  <form class="report-filter-bar" @submit.prevent="emit('search')">
    <label>
      所属月度
      <input
        :value="monthKey"
        type="month"
        @input="emit('update:monthKey', ($event.target as HTMLInputElement).value)"
      />
    </label>
    <label class="period-range-field">
      周报周期
      <div class="period-range-picker">
        <button
          class="period-range-picker__trigger"
          type="button"
          aria-label="选择周报周期"
          @click="openPeriodPicker"
        >
          <output class="period-range-picker__display">
            {{ periodStart && periodEnd ? `${periodStart} 至 ${periodEnd}` : "选择周期" }}
          </output>
        </button>
        <input
          ref="periodInput"
          class="period-range-picker__input"
          :value="periodStart"
          min="1900-01-01"
          step="7"
          type="date"
          tabindex="-1"
          aria-hidden="true"
          @change="updatePeriodStart(($event.target as HTMLInputElement).value)"
        />
      </div>
    </label>
    <label class="role-filter">职位<RoleFilterSelect :model-value="roleCode" @update:model-value="emit('update:roleCode', $event)" /></label>
    <label v-if="showGroup" class="group-filter">
      分组
      <GroupTreeSelect
        :model-value="groupId || null"
        :groups="groupOptions"
        empty-label="全部分组"
        @update:model-value="emit('update:groupId', $event || '')"
      />
    </label>
    <label v-if="showPerson" class="person-filter">人员<PersonSelect :model-value="employeeId" :users="userOptions" @update:model-value="emit('update:employeeId',String($event || ''))" /></label>
    <label v-if="showName">姓名<input :value="employeeName || ''" maxlength="128" placeholder="请输入姓名" @input="emit('update:employeeName', ($event.target as HTMLInputElement).value)" /></label>
    <div class="report-filter-actions">
      <button class="primary-button" type="submit">查询</button>
      <button class="ghost-button" type="button" @click="emit('reset')">重置</button>
    </div>
  </form>
</template>

<style scoped src="./ReportFilterBar.css"></style>
