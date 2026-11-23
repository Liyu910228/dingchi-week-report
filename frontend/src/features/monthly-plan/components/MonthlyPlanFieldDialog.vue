<script setup lang="ts">
import BaseDialog from "@/components/overlay/BaseDialog.vue"
import type { TaskFieldDefinition } from "@/features/weekly-report/task-draft"
defineProps<{ open: boolean; fields: TaskFieldDefinition[] }>()
const selected = defineModel<string[]>({ required: true })
const emit = defineEmits<{ close: [] }>()
</script>
<template>
  <BaseDialog :open="open" title="选择展示字段" width="620px" @close="emit('close')">
    <div class="column-options"><label v-for="field in fields" :key="field.code"><input v-model="selected" type="checkbox" :value="field.code" />{{ field.label }}</label></div>
    <template #actions><button class="primary-button" type="button" @click="emit('close')">确定</button></template>
  </BaseDialog>
</template>
<style scoped src="./MonthlyPlanFieldDialog.css"></style>
