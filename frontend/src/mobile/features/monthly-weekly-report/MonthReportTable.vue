<script setup lang="ts">
import { vRowBackgrounds } from "@/shared/table/row-backgrounds";
import { formatDateTime } from "@/utils/date";
import type { MonthRow } from "./types";
defineProps<{
    rows: MonthRow[];
}>();
const emit = defineEmits<{
    open: [
        row: MonthRow
    ];
}>();
</script>

<template>
  <div class="report-list-table-wrap">
    <table data-mobile-cards v-row-backgrounds class="report-list-table">
      <thead><tr>
        <th data-column-key="month_key">所属月度</th><th data-column-key="employee_name">人员</th><th data-column-key="role_code">职位</th><th data-column-key="week_count">已填写周数</th>
        <th data-column-key="completed_count">已提交周数</th><th data-column-key="updated_at">最近更新时间</th>
      </tr></thead>
      <tbody>
        <tr v-for="row in rows" :key="row.employee_id + row.month_key" class="month-report-card"
          role="link" tabindex="0" :aria-label="`查看${row.employee_name} ${row.month_key}月度周报`"
          @click="emit('open', row)" @keydown.enter.prevent="emit('open', row)"
          @keydown.space.prevent="emit('open', row)">
          <td data-label="所属月度" class="period-cell"><strong>{{ row.month_key }}</strong></td>
          <td data-label="人员">{{ row.employee_name }}</td>
          <td data-label="职位">{{ row.role_name }}</td>
          <td data-label="已填写周数">{{ row.week_count }}</td>
          <td data-label="已提交周数">{{ row.completed_count }}</td>
          <td data-label="最近更新时间" class="date-cell">{{ formatDateTime(row.updated_at) }}</td>
        </tr>
        <tr v-if="!rows.length"><td colspan="6" class="empty-row">暂无月度周报</td></tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped src="./MonthReportTable.css"></style>
