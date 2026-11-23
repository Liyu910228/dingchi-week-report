<script setup lang="ts">
import CustomerTabsHeader from "@/features/submissions/components/CustomerTabsHeader.vue"
import FullscreenPanel from "@/components/layout/FullscreenPanel.vue"
import ExamplePreviewButton from "@/components/feedback/ExamplePreviewButton.vue"
import BaseDialog from "@/components/overlay/BaseDialog.vue"
import PaginationBar from "@/components/navigation/PaginationBar.vue"
import EditableTaskTable from "@/features/weekly-report/components/EditableTaskTable.vue"
import TaskQuickFillDialog from "@/features/weekly-report/components/TaskQuickFillDialog.vue"
import { recruitmentTaskTemplates } from "@/features/weekly-report/recruitment/task-templates"
import { recruitmentWeeklyTaskSample, recruitmentWeeklyTaskSampleFields } from "@/features/weekly-report/recruitment/samples"
import type { RecruitmentTaskDraft } from "@/features/weekly-report/recruitment/types"
import { useRecruitmentTaskCollection, type RecruitmentCollectionProps } from "@/features/weekly-report/recruitment/useRecruitmentTaskCollection"
const props = defineProps<RecruitmentCollectionProps>()
const emit = defineEmits<{ "update:tasks": [tasks: RecruitmentTaskDraft[]] }>()
const { quickFillOpen, columnsOpen, users, dimensionFilter, plannedDateFilter, taskPage, pageSize, selectedColumns, dimensionOptions, filteredTaskEntries, totalPages, pagedTaskEntries, availableFields, selectedFields, addTemplates, insertTask, patchTask, removeTask } = useRecruitmentTaskCollection(props, emit)
</script>
<template>
  <FullscreenPanel :title="title" class="dashboard-card task-section">
    <template #tabs><CustomerTabsHeader /></template>
    <template #actions>
      <ExamplePreviewButton :content="recruitmentWeeklyTaskSample" :fields="recruitmentWeeklyTaskSampleFields" panel-title="本周工作任务填写样例" />
      <button class="ghost-button" type="button" @click="columnsOpen = true">选择展示字段</button>
      <button class="primary-button" type="button" @click="quickFillOpen = true">新增任务</button>
    </template>
    <div class="task-section__filters">
      <select v-model="dimensionFilter" aria-label="按维度筛选"><option value="">全部维度</option><option v-for="dimension in dimensionOptions" :key="dimension" :value="dimension">{{ dimension }}</option></select>
      <label><span>计划完成时间</span><input v-model="plannedDateFilter" type="date" aria-label="按计划完成时间筛选" /></label>
    </div>
    <EditableTaskTable template-code="recruitment_v1" recruitment-mode scope-field="dimension" :total-tasks="tasks.length" @add-blank="insertTask(-1)" :entries="pagedTaskEntries" :fields="selectedFields" :users="users" :offset="(taskPage - 1) * pageSize" :templates="recruitmentTaskTemplates" @patch="patchTask" @remove="removeTask" @insert="insertTask" />
    <PaginationBar :page="taskPage" :page-size="pageSize" :total="filteredTaskEntries.length" :total-pages="totalPages" @change="taskPage = $event" />
  </FullscreenPanel>
  <TaskQuickFillDialog :open="quickFillOpen" recruitment :templates="recruitmentTaskTemplates" @close="quickFillOpen = false" @confirm="addTemplates" />
  <BaseDialog :open="columnsOpen" title="选择展示字段" width="640px" @close="columnsOpen = false">
    <div class="column-options"><label v-for="field in availableFields" :key="field.code"><input v-model="selectedColumns" :value="field.code" type="checkbox" />{{ field.label }}</label></div>
    <template #actions><button class="primary-button" type="button" @click="columnsOpen = false">确定</button></template>
  </BaseDialog>
</template>
<style scoped src="./TaskCollectionSection.css"></style>
