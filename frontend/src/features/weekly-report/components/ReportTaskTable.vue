<script setup lang="ts">
import ScrollableTabs from "@/components/navigation/ScrollableTabs.vue"
import { vRowBackgrounds } from "@/shared/table/row-backgrounds"
import { vResizableColumns } from "@/shared/table/resizable-columns"
import { useTaskTableResizeKey } from "@/features/weekly-report/useTaskTableResizeKey"
import BaseDialog from "@/components/overlay/BaseDialog.vue"
import { useReportTaskTable, type ReportTaskTableProps } from "../composables/useReportTaskTable"
import ReportPagination from "./ReportPagination.vue"
import ReportTaskDetailDialog from "./ReportTaskDetailDialog.vue"
const props = withDefaults(defineProps<ReportTaskTableProps>(), { showColumnsButton: true, showCustomerTabs: true })
const resizeKey = useTaskTableResizeKey("weekly", () => props.templateCode)
const {
  sharedMode, deliveryMode, customers, activeCustomer, columnsOpen, selectedCodes, detailOpen, detailItem,
  page, pageSize, availableFields, primaryField, displayItems, totalPages, pagedItems, selectedFields,
  customerRowspan, primaryValue, statusClass, taskStatus, openTask, itemAttachments, openColumns,
  sharedRowspan, formatReportTaskField, reportTaskStatusLabel, reportTaskUpdatedAt,
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
      <table v-row-backgrounds v-resizable-columns="resizeKey" class="report-task-table__grid">
        <thead>
          <tr>
            <th class="fixed-col serial-col" data-column-key="serial">序号</th>
            <th :data-column-key="primaryField.field_code" v-if="primaryField" class="fixed-col customer-col">{{ primaryField.label }}</th>
            <th
              data-column-key="task_name" class="fixed-col task-col"
              :class="{ 'task-col--without-primary': !primaryField }"
            >{{ props.fields?.find(field => field.field_code === 'task_name')?.label || '工作任务' }}</th>
            <th :data-column-key="field.field_code" v-for="field in selectedFields" :key="field.field_code" class="dynamic-col"
              :class="{ 'multiline-col': ['work_content', 'output_description'].includes(field.field_code) }">
              {{ field.label }}
            </th>
            <th class="fixed-col status-col" data-column-key="status">状态</th>
            <th class="fixed-col updated-col" data-column-key="updated_at">更新时间</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="(item, index) in pagedItems" :key="item.id || `${item.task_code}-${index}`">
            <tr>
              <td class="fixed-col serial-col">{{ (page - 1) * pageSize + index + 1 }}</td>
              <td
                v-if="primaryField && customerRowspan(index) > 0"
                class="fixed-col customer-col customer-cell"
                :rowspan="customerRowspan(index)"
              >
                <span class="cell-text user-content" :title="primaryValue(item)">
                  {{ primaryValue(item) }}
                </span>
              </td>
              <td
                v-if="sharedRowspan(index) > 0" :rowspan="sharedRowspan(index)"
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
              </td>
              <template v-for="field in selectedFields" :key="field.field_code">
                <td v-if="field.field_code !== 'work_content' || sharedRowspan(index, true) > 0"
                  :rowspan="field.field_code === 'work_content' ? sharedRowspan(index, true) : 1"
                  class="dynamic-col" :class="{ 'multiline-col': ['work_content', 'output_description'].includes(field.field_code) }">
                  <span
                    class="cell-text" :class="{'user-content':field.field_code!=='on_time_status'}"
                    :title="formatReportTaskField(item, field.field_code)"
                  >
                    {{ formatReportTaskField(item, field.field_code) }}
                  </span>
                  <button v-if="sharedMode && field.field_code === 'document_links' && itemAttachments(item).length"
                    class="task-link attachment-link" type="button" @click="openTask(item)">查看附件（{{ itemAttachments(item).length }}）</button>
                </td>
              </template>
              <td class="fixed-col status-col">
                <span
                  class="status-pill"
                  :class="`status-pill--${statusClass(taskStatus(item))}`"
                >
                  {{ reportTaskStatusLabel(taskStatus(item)) }}
                </span>
              </td>
              <td class="fixed-col updated-col date-cell">
                {{ reportTaskUpdatedAt(item) }}
              </td>
            </tr>
          </template>
          <tr v-if="!pagedItems.length">
            <td :colspan="selectedFields.length + (primaryField ? 5 : 4)" class="empty-cell">暂无工作任务</td>
          </tr>
        </tbody>
      </table>
    </div>
    <ReportPagination
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
