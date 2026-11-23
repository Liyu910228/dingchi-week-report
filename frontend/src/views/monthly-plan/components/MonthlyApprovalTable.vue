<script setup lang="ts">
import { vRowBackgrounds } from "@/shared/table/row-backgrounds"
import { vResizableColumns } from "@/shared/table/resizable-columns"
import { useUserTableResizeKey } from "@/features/auth/useUserTableResizeKey"
import MonthlyGoalSummary from "@/features/monthly-plan/components/MonthlyGoalSummary.vue"
import PlanStatusTag from "@/features/monthly-plan/components/PlanStatusTag.vue"
import { type ApprovalRecord } from "@/features/monthly-plan/types"
import { formatDateTime } from "@/utils/date"
defineProps<{ records: ApprovalRecord[]; busy: boolean }>()
defineEmits<{ view:[record:ApprovalRecord] }>()
const resizeKey = useUserTableResizeKey(() => `monthly-approvals`)
</script>

<template>
  <div class="approval-table-wrap">
    <table v-row-backgrounds v-resizable-columns="resizeKey" class="approval-table">
      <thead><tr><th data-column-key="month_key">所属月度</th><th data-column-key="employee_name">提交人</th><th data-column-key="role_code">职位</th><th data-column-key="group_name">分组</th><th data-column-key="summary">月度目标</th><th data-column-key="process_type">申请类型</th><th data-column-key="revision">版本</th><th data-column-key="status">流程状态</th><th data-column-key="created_at">提交时间</th><th data-column-key="my_acted_at">处理时间</th><th data-column-key="actions">操作</th></tr></thead>
      <tbody>
        <tr v-for="record in records" :key="record.id">
          <td>{{record.month_key}}</td><td>{{record.employee_name}}</td><td>{{record.role_name || record.role_code || "—"}}</td><td>{{record.group_name}}</td><td class="summary"><MonthlyGoalSummary :summary="record.snapshot.summary" :sections="record.snapshot.parts?.map(part => ({role_code:part.role_code,role_name:part.role_name,summary:part.payload.summary || ''}))" /></td><td>{{record.process_type==='change'?'变更申请':'首次申请'}}</td><td>{{record.revision}}</td>
          <td><PlanStatusTag :status="record.status" /></td>
          <td class="date">{{formatDateTime(record.created_at)}}</td><td class="date">{{formatDateTime(record.completed_at)}}</td>
          <td class="actions"><button type="button" @click="$emit('view',record)">查看</button></td>
        </tr>
        <tr v-if="!records.length"><td class="empty" colspan="11">{{busy?'正在加载审批任务…':'暂无符合条件的审批任务'}}</td></tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped src="./MonthlyApprovalTable.css"></style>
