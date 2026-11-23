<script setup lang="ts">
import { computed } from "vue"

import SearchableSelect from "@/mobile/components/form/SearchableSelect.vue"
import type { DirectoryUserOption } from "../types"

const props = defineProps<{
  modelValue: string | string[] | null
  users: DirectoryUserOption[]
  multiple?: boolean
  disabled?: boolean
  ariaLabel?: string
  placeholder?: string
  ordered?: boolean
}>()
const emit = defineEmits<{ "update:modelValue": [value: string | string[]] }>()
const options = computed(() => props.users.map((user) => ({
  value: user.id, label: user.display_name,
  description: [user.employee_no, user.username].filter(Boolean).join(" · "),
  group: user.group_name || "未分组",
})).sort((a, b) => a.group.localeCompare(b.group, "zh-CN") || a.label.localeCompare(b.label, "zh-CN")))
</script>

<template>
  <SearchableSelect
    teleport-menu
    menu-class="person-select-menu"
    :model-value="modelValue || (multiple ? [] : '')"
    :options="options"
    :multiple="multiple"
    :disabled="disabled"
    :show-selection-order="ordered"
    :aria-label="ariaLabel || '选择人员'"
    :placeholder="placeholder || '按姓名、账号、工号或分组搜索'"
    @update:model-value="emit('update:modelValue', $event)"
  />
</template>

<style scoped src="./PersonSelect.css"></style>
