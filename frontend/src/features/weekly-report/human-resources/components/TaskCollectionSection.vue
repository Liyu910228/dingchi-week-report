<script setup lang="ts">
import CustomerTabsHeader from "@/features/submissions/components/CustomerTabsHeader.vue"
import FullscreenPanel from "@/components/layout/FullscreenPanel.vue"
import ExamplePreviewButton from "@/components/feedback/ExamplePreviewButton.vue"
import BaseDialog from "@/components/overlay/BaseDialog.vue"
import PaginationBar from "@/components/navigation/PaginationBar.vue"
import EditableTaskTable from "@/features/weekly-report/human-resources/components/EditableTaskTable.vue"
import TaskQuickFillDialog from "@/features/weekly-report/human-resources/components/TaskQuickFillDialog.vue"
import { humanResourcesTaskTemplates } from "@/features/weekly-report/human-resources/task-templates"
import { humanResourcesWeeklyTaskSample, humanResourcesWeeklyTaskSampleFields } from "@/features/weekly-report/human-resources/samples"
import type { HumanResourcesTaskDraft } from "@/features/weekly-report/human-resources/types"
import { useHumanResourcesTaskCollection, type HumanResourcesCollectionProps } from "@/features/weekly-report/human-resources/useHumanResourcesTaskCollection"
const props = defineProps<HumanResourcesCollectionProps>()
const emit = defineEmits<{ "update:tasks": [tasks: HumanResourcesTaskDraft[]] }>()
const { quickFillOpen, columnsOpen, users, dimensionFilter, plannedDateFilter, taskPage, pageSize, selectedColumns, dimensionOptions, filteredTaskEntries, totalPages, pagedTaskEntries, availableFields, selectedFields, addTemplates, insertTask, patchTask, removeTask } = useHumanResourcesTaskCollection(props, emit)
</script>
<template>
  <FullscreenPanel :title="title" class="dashboard-card task-section">
    <template #tabs><CustomerTabsHeader /></template>
    <template #actions>
      <ExamplePreviewButton :content="humanResourcesWeeklyTaskSample" :fields="humanResourcesWeeklyTaskSampleFields" panel-title="本周工作任务填写样例" />
      <button class="ghost-button" type="button" @click="columnsOpen = true">选择展示字段</button>
      <button class="primary-button" type="button" @click="quickFillOpen = true">新增任务</button>
    </template>
    <div class="task-section__filters">
      <select v-model="dimensionFilter" aria-label="按模块筛选"><option value="">全部模块</option><option v-for="dimension in dimensionOptions" :key="dimension" :value="dimension">{{ dimension }}</option></select>
      <label><span>计划完成时间</span><input v-model="plannedDateFilter" type="date" aria-label="按计划完成时间筛选" /></label>
    </div>
    <EditableTaskTable human-resources-mode scope-field="dimension" :total-tasks="tasks.length" @add-blank="insertTask(-1)" :entries="pagedTaskEntries" :fields="selectedFields" :users="users" :offset="(taskPage - 1) * pageSize" :templates="humanResourcesTaskTemplates" @patch="patchTask" @remove="removeTask" @insert="insertTask" />
    <PaginationBar :page="taskPage" :page-size="pageSize" :total="filteredTaskEntries.length" :total-pages="totalPages" @change="taskPage = $event" />
  </FullscreenPanel>
  <TaskQuickFillDialog :open="quickFillOpen" human-resources :templates="humanResourcesTaskTemplates" @close="quickFillOpen = false" @confirm="addTemplates" />
  <BaseDialog :open="columnsOpen" title="选择展示字段" width="640px" @close="columnsOpen = false">
    <div class="column-options"><label v-for="field in availableFields" :key="field.code"><input v-model="selectedColumns" :value="field.code" type="checkbox" />{{ field.label }}</label></div>
    <template #actions><button class="primary-button" type="button" @click="columnsOpen = false">确定</button></template>
  </BaseDialog>
</template>
<style scoped src="./TaskCollectionSection.css"></style>
