<script setup lang="ts">
import AttachmentDownloadLink from "@/mobile/components/file/AttachmentDownloadLink.vue"
import { computed } from "vue"
import type { PlanSnapshot } from "../types"
import { monthlyPlanScopeLabel } from "@/mobile/features/weekly-report/monthly-plan/template-fields"
const props=defineProps<{before:PlanSnapshot;after:PlanSnapshot}>()
const scope=computed(()=>monthlyPlanScopeLabel(props.after.template_code))
const rows=computed(()=>{
 const original=new Map(props.before.tasks.map(task=>[task.id,task]))
 const proposed=new Map(props.after.tasks.map(task=>[task.id,task]))
 return [...new Set([...original.keys(),...proposed.keys()])].map(id=>{
  const before=original.get(id),after=proposed.get(id)
  const state=!before?'新增':!after?'删除':before.work_task!==after.work_task || before.scope_name!==after.scope_name || (before.work_content || "")!==(after.work_content || "") || JSON.stringify(before.attachments || [])!==JSON.stringify(after.attachments || [])?'修改':'未变更'
  return {id,before,after,state}
 })
})
</script>
<template>
<section class="dashboard-card plan-comparison">
 <div class="comparison-heading"><h2>原生效版本</h2><h2>申请变更版本</h2></div>
 <div class="comparison-pair" :class="{'is-changed':before.summary!==after.summary}"><div><h3>月度目标</h3><p class="user-content">{{before.summary}}</p></div><div><h3>月度目标 <span v-if="before.summary!==after.summary">修改</span></h3><p class="user-content">{{after.summary}}</p></div></div>
 <div v-for="(row,index) in rows" :key="row.id" class="comparison-pair" :class="{'is-changed':row.state!=='未变更','is-added':row.state==='新增','is-deleted':row.state==='删除'}">
  <div><h3>计划 {{index+1}}</h3><template v-if="row.before"><p class="user-content" v-if="scope"><strong>{{scope}}：</strong>{{row.before.scope_name}}</p><p class="user-content">{{row.before.work_task}}</p><p class="user-content" v-if="row.before.work_content">{{row.before.work_content}}</p><div v-for="file in row.before.attachments" :key="file.id"><AttachmentDownloadLink :attachment-id="file.id" :file-name="file.file_name" /></div></template><p v-else>—</p></div>
  <div><h3>计划 {{index+1}} <span v-if="row.state!=='未变更'">{{row.state}}</span></h3><template v-if="row.after"><p class="user-content" v-if="scope"><strong>{{scope}}：</strong>{{row.after.scope_name}}</p><p class="user-content">{{row.after.work_task}}</p><p class="user-content" v-if="row.after.work_content">{{row.after.work_content}}</p><div v-for="file in row.after.attachments" :key="file.id"><AttachmentDownloadLink :attachment-id="file.id" :file-name="file.file_name" /></div></template><p v-else>已删除</p></div>
 </div>
</section>
</template>
<style scoped src="./PlanComparison.css"></style>
