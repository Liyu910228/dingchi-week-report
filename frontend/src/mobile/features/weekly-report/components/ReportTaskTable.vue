<script setup lang="ts">
import ScrollableTabs from "@/mobile/components/navigation/ScrollableTabs.vue"
import TaskHierarchy from "@/mobile/components/data-display/TaskHierarchy.vue"
import BaseDialog from "@/mobile/components/overlay/BaseDialog.vue"
import { useReportTaskTable, type ReportTaskTableProps } from "../composables/useReportTaskTable"
import ScrollLoadMore from "@/mobile/components/navigation/ScrollLoadMore.vue"
import ReportTaskDetailDialog from "./ReportTaskDetailDialog.vue"
const props = withDefaults(defineProps<ReportTaskTableProps>(), { showColumnsButton: true, showCustomerTabs: true })
const {
  sharedMode, deliveryMode, customers, activeCustomer, columnsOpen, selectedCodes, detailOpen, detailItem,
  page, pageSize, availableFields, primaryField, displayItems, totalPages, pagedItems, selectedFields,
  sharedKey, primaryValue, statusClass, taskStatus, openTask, itemAttachments, openColumns,
  formatReportTaskField, reportTaskStatusLabel, reportTaskUpdatedAt,
} = useReportTaskTable(props)
defineExpose({ openColumns, customers, activeCustomer, deliveryMode })
</script>

<template>
  <div class="report-task-table" :class="{ 'report-task-table--delivery': sharedMode }">
    <ScrollableTabs v-if="showCustomerTabs !== false && deliveryMode && customers.length" v-model="activeCustomer" :items="customers" aria-label="客户" />
    <div v-if="showColumnsButton" class="report-task-table__toolbar">
      <button class="ghost-button" type="button" @click="columnsOpen = true">选择展示字段</button>
    </div>

    <div class="report-task-table-wrap">
      <div class="mobile-task-cards">


          <TaskHierarchy :rows="pagedItems" :row-key="row => String(row.id || row.task_code)" :task-key="row => sharedKey(row,false)" :content-key="row => sharedKey(row,true)" :title="row => formatReportTaskField(row,'task_name')">
<template #task="{row:item,index}">

              <div data-card-field :data-label="primaryField?.label || '客户'"
                v-if="primaryField"
                class="fixed-col customer-col customer-cell"

              >
                <span class="cell-text user-content" :title="primaryValue(item)">
                  {{ primaryValue(item) }}
                </span>
              </div>
              <div data-card-field data-label="工作任务"

                class="fixed-col task-col task-cell"
                :class="{ 'task-col--without-primary': !primaryField }"
              >
                <span v-if="sharedMode" class="cell-text user-content">{{ formatReportTaskField(item, "task_name") }}</span>
                <button v-else
                  class="task-link user-content"
                  type="button"
                  :title="item.task_name_snapshot || item.task_code"
                  @click="openTask(item)"
                >
                  {{ item.task_name_snapshot || item.task_code || "—" }}
                </button>
              </div>
              </template>
<template #content="{row:item,index}"><template v-for="field in selectedFields.filter(item => item.field_code === 'work_content')" :key="field.field_code">
                <div data-card-field :data-label="field.label"

                  class="dynamic-col" :class="{ 'multiline-col': ['work_content', 'output_description'].includes(field.field_code) }">
                  <span
                    class="cell-text" :class="{'user-content':field.field_code!=='on_time_status'}"
                    :title="formatReportTaskField(item, field.field_code)"
                  >
                    {{ formatReportTaskField(item, field.field_code) }}
                  </span>
                  <button v-if="sharedMode && field.field_code === 'document_links' && itemAttachments(item).length"
                    class="task-link attachment-link" type="button" @click="openTask(item)">查看附件（{{ itemAttachments(item).length }}）</button>
                </div>
              </template>
              </template>
<template #row="{row:item,index}"><template v-for="field in selectedFields.filter(item => item.field_code !== 'work_content')" :key="field.field_code">
                <div data-card-field :data-label="field.label"

                  class="dynamic-col" :class="{ 'multiline-col': ['work_content', 'output_description'].includes(field.field_code) }">
                  <span
                    class="cell-text" :class="{'user-content':field.field_code!=='on_time_status'}"
                    :title="formatReportTaskField(item, field.field_code)"
                  >
                    {{ formatReportTaskField(item, field.field_code) }}
                  </span>
                  <button v-if="sharedMode && field.field_code === 'document_links' && itemAttachments(item).length"
                    class="task-link attachment-link" type="button" @click="openTask(item)">查看附件（{{ itemAttachments(item).length }}）</button>
                </div>
              </template>
              <div data-card-field data-label="状态" class="fixed-col status-col">
                <span
                  class="status-pill"
                  :class="`status-pill--${statusClass(taskStatus(item))}`"
                >
                  {{ reportTaskStatusLabel(taskStatus(item)) }}
                </span>
              </div>
              <div data-card-field data-label="更新时间" class="fixed-col updated-col date-cell">
                {{ reportTaskUpdatedAt(item) }}
              </div>
            </template>
</TaskHierarchy>
          <article data-mobile-task-card v-if="!pagedItems.length">
            <div data-card-field data-label="" :colspan="selectedFields.length + (primaryField ? 5 : 4)" class="empty-cell">暂无工作任务</div>
          </article>

      </div>
    </div>
    <ScrollLoadMore :show-end="false"
      :page="page"
      :page-size="pageSize"
      :total="displayItems.length"
      :total-pages="totalPages"
      @change="page = $event"
    />
  </div>

  <BaseDialog
    :open="columnsOpen"
    title="选择展示字段"
    width="640px"
    @close="columnsOpen = false"
  >
    <div class="column-options">
      <label v-for="field in availableFields" :key="field.field_code">
        <input v-model="selectedCodes" :value="field.field_code" type="checkbox" />
        <span>{{ field.label }}</span>
      </label>
      <p v-if="!availableFields.length" class="column-options__empty">暂无可选字段</p>
    </div>
    <template #actions>
      <button class="primary-button" type="button" @click="columnsOpen = false">确定</button>
    </template>
  </BaseDialog>

  <ReportTaskDetailDialog
    :open="detailOpen"
    :item="detailItem"
    :fields="props.fields"
    :attachments="detailItem ? itemAttachments(detailItem) : []"
    @close="detailOpen = false"
  />
</template>

<style scoped src="./ReportTaskTable.css"></style>

<style scoped src="@/mobile/components/data-display/TaskCards.css"></style>
