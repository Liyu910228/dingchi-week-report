<script setup lang="ts">
import BaseDialog from "@/mobile/components/overlay/BaseDialog.vue"
import type { TaskFieldDefinition } from "@/mobile/features/weekly-report/task-draft"
defineProps<{ open: boolean; fields: TaskFieldDefinition[]; error?: string }>()
const selected = defineModel<string[]>({ required: true })
const emit = defineEmits<{ close: []; retry: [] }>()
</script>
<template>
  <BaseDialog :open="open" title="选择展示字段" width="620px" @close="emit('close')">
    <p v-if="error" role="alert" class="field-error">{{error}} <button type="button" @click="emit('retry')">重试</button></p>
    <p v-if="!fields.length && !error" role="status">当前模板暂无可选展示字段。</p>
    <div class="column-options"><label v-for="field in fields" :key="field.code"><input v-model="selected" type="checkbox" :value="field.code" />{{ field.label }}</label></div>
    <template #actions><button class="primary-button" type="button" @click="emit('close')">确定</button></template>
  </BaseDialog>
</template>
<style scoped src="./MonthlyPlanFieldDialog.css"></style>
