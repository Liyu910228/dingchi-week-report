<script setup lang="ts">
import CustomerTabsHeader from "@/features/submissions/components/CustomerTabsHeader.vue"
import {inject} from "vue"
import {customerScopeKey} from "@/features/submissions/customer-scope"
const customerScope=inject(customerScopeKey,undefined)
import DeliveryCustomerSelect from "./DeliveryCustomerSelect.vue"
import ScrollableTabs from "@/components/navigation/ScrollableTabs.vue"
import FullscreenPanel from "@/components/layout/FullscreenPanel.vue"
import ExamplePreviewButton from "@/components/feedback/ExamplePreviewButton.vue"
import BaseDialog from "@/components/overlay/BaseDialog.vue"
import type { TaskDraft } from "@/features/weekly-report/task-draft"
import DeliveryQuickFillDialog from "@/features/weekly-report/components/TaskQuickFillDialog.vue"
import DeliveryEditableTaskTable from "@/features/weekly-report/components/EditableTaskTable.vue"
import ReportPagination from "@/components/navigation/PaginationBar.vue"
import { useTaskCollection, type DeliveryTaskCollectionProps } from "@/features/weekly-report/composables/useDeliveryTaskCollection"
const props = withDefaults(defineProps<DeliveryTaskCollectionProps>(), {
  includeCustomer: true,
  sampleContent: "",
  sampleFields: () => [],
  columnPreferenceKey: "delivery_specialist_v1",
})
const emit = defineEmits<{ "update:tasks": [tasks: TaskDraft[]] }>()
const { assignCustomer, addTemplates, filteredTaskEntries, quickFillOpen, columnsOpen, users, customerFilter, plannedDateFilter, taskPage, taskPageSize, showCustomer, editableDelivery, customerOptions, selectedColumns, availableFields, selectedFields, totalTaskPages, pagedTaskEntries, addTask, removeTask, patchTask, insertTask } = useTaskCollection(props, emit)
</script>

<template>
  <FullscreenPanel :title="title" class="dashboard-card task-section">
    <template #tabs><CustomerTabsHeader />
      <ScrollableTabs v-if="!customerScope?.enabled.value && editableDelivery && customerOptions.length" v-model="customerFilter"
        :items="customerOptions.map(customer => ({ id: customer, name: customer || '未选择客户' }))" />
    </template>
    <template #actions>
        <ExamplePreviewButton
          :content="sampleContent"
          :fields="sampleFields"
          panel-title="本周工作任务填写样例"
        />
        <button class="ghost-button" type="button" @click="columnsOpen = true">选择展示字段</button>
        <button class="primary-button" type="button" @click="addTask">新增任务</button>
    </template>
    <div class="task-section__filters">
      <label v-if="editableDelivery && customerOptions.includes('') && customerFilter === ''" class="unassigned-customer"><span>客户</span><DeliveryCustomerSelect model-value="" required @update:model-value="assignCustomer" /></label>
      <select v-if="showCustomer && !editableDelivery" v-model="customerFilter" aria-label="按客户筛选">
        <option value="">全部客户</option>
        <option v-for="customer in customerOptions" :key="customer" :value="customer">{{ customer }}</option>
      </select>
      <label>
        <span>计划完成时间</span>
        <input v-model="plannedDateFilter" type="date" aria-label="按计划完成时间筛选" />
      </label>
    </div>
    <DeliveryEditableTaskTable :template-code="columnPreferenceKey" delivery-mode :total-tasks="tasks.length" @add-blank="insertTask(-1)" :entries="pagedTaskEntries" :fields="selectedFields" :users="users" :templates="templates" :offset="(taskPage - 1) * taskPageSize" @patch="patchTask" @insert="(index, shared) => insertTask(index, shared === 'dimension' || shared === 'customer_name' ? undefined : shared)" @remove="removeTask" />
    <ReportPagination
      :page="taskPage"
      :page-size="taskPageSize"
      :total="filteredTaskEntries.length"
      :total-pages="totalTaskPages"
      @change="taskPage = $event"
    />
  </FullscreenPanel>

  <DeliveryQuickFillDialog :scope-less="!showCustomer" :templates="templates" :open="quickFillOpen" @close="quickFillOpen = false" @confirm="addTemplates" />
  <BaseDialog :open="columnsOpen" title="选择展示字段" width="620px" @close="columnsOpen = false">
    <div class="column-options">
      <label v-for="field in availableFields" :key="field.code"><input v-model="selectedColumns" :value="field.code" type="checkbox" />{{ field.label }}</label>
    </div>
    <template #actions><button class="primary-button" type="button" @click="columnsOpen = false">确定</button></template>
  </BaseDialog>
</template>

<style scoped src="./DeliveryTaskCollectionSection.css"></style>
