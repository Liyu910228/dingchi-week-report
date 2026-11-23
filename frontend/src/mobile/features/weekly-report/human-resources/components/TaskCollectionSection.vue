<script setup lang="ts">
import TaskAddFooter from "@/mobile/features/weekly-report/components/TaskAddFooter.vue"
import CollapsibleFilters from "@/mobile/components/form/CollapsibleFilters.vue"
import CustomerTabsHeader from "@/mobile/features/submissions/components/CustomerTabsHeader.vue"
import FullscreenPanel from "@/mobile/components/layout/FullscreenPanel.vue"
import ExamplePreviewButton from "@/mobile/components/feedback/ExamplePreviewButton.vue"
import BaseDialog from "@/mobile/components/overlay/BaseDialog.vue"
import ScrollLoadMore from "@/mobile/components/navigation/ScrollLoadMore.vue"
import EditableTaskTable from "@/mobile/features/weekly-report/human-resources/components/EditableTaskTable.vue"
import TaskQuickFillDialog from "@/mobile/features/weekly-report/human-resources/components/TaskQuickFillDialog.vue"
import { humanResourcesTaskTemplates } from "@/mobile/features/weekly-report/human-resources/task-templates"
import { humanResourcesWeeklyTaskSample, humanResourcesWeeklyTaskSampleFields } from "@/mobile/features/weekly-report/human-resources/samples"
import type { HumanResourcesTaskDraft } from "@/mobile/features/weekly-report/human-resources/types"
import { useHumanResourcesTaskCollection, type HumanResourcesCollectionProps } from "@/mobile/features/weekly-report/human-resources/useHumanResourcesTaskCollection"
const props = defineProps<HumanResourcesCollectionProps>()
const emit = defineEmits<{ "update:tasks": [tasks: HumanResourcesTaskDraft[]] }>()
const { quickFillOpen, columnsOpen, users, dimensionFilter, plannedDateFilter, taskPage, pageSize, selectedColumns, dimensionOptions, filteredTaskEntries, totalPages, pagedTaskEntries, availableFields, selectedFields, addTemplates, insertTask, patchTask, removeTask } = useHumanResourcesTaskCollection(props, emit)
</script>
<template>
  <FullscreenPanel :title="title" class="dashboard-card task-section">
    <template #tabs><CustomerTabsHeader /></template>
    <template #primary><button class="primary-button" type="button" @click="quickFillOpen = true">新增任务</button></template>
    <template #actions>
      <ExamplePreviewButton :content="humanResourcesWeeklyTaskSample" :fields="humanResourcesWeeklyTaskSampleFields" panel-title="本周工作任务填写样例" />
      <button class="ghost-button" type="button" @click="columnsOpen = true">选择展示字段</button>
      
    </template>
    <CollapsibleFilters class="task-filter-panel"><div class="task-section__filters filter-panel-form">
      <select v-model="dimensionFilter" aria-label="按模块筛选"><option value="">全部模块</option><option v-for="dimension in dimensionOptions" :key="dimension" :value="dimension">{{ dimension }}</option></select>
      <label><span>计划完成时间</span><input v-model="plannedDateFilter" type="date" aria-label="按计划完成时间筛选" /></label>
    </div></CollapsibleFilters>
    <EditableTaskTable human-resources-mode scope-field="dimension" :total-tasks="tasks.length" @add-blank="insertTask(-1)" :all-tasks="tasks" @remove-many="keys => emit('update:tasks', tasks.filter(task => !keys.includes(task.client_key)))" :entries="pagedTaskEntries" :fields="selectedFields" :users="users" :offset="0" :templates="humanResourcesTaskTemplates" @patch="patchTask" @remove="removeTask" @insert="insertTask" />
    <ScrollLoadMore :show-end="false"  :page="taskPage" :page-size="pageSize" :total="filteredTaskEntries.length" :total-pages="totalPages" @change="taskPage = $event" />
    <TaskAddFooter @add="insertTask(tasks.length)" />
  </FullscreenPanel>
  <TaskQuickFillDialog :open="quickFillOpen" human-resources :templates="humanResourcesTaskTemplates" @close="quickFillOpen = false" @confirm="addTemplates" />
  <BaseDialog :open="columnsOpen" title="选择展示字段" width="640px" @close="columnsOpen = false">
    <div class="column-options"><label v-for="field in availableFields" :key="field.code"><input v-model="selectedColumns" :value="field.code" type="checkbox" />{{ field.label }}</label></div>
    <template #actions><button class="primary-button" type="button" @click="columnsOpen = false">确定</button></template>
  </BaseDialog>
</template>
<style scoped src="./TaskCollectionSection.css"></style>






