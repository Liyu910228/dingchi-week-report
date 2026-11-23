<script setup lang="ts">
import { computed } from "vue"
import { buildApprovalFlow } from "@/mobile/features/monthly-plan/approval-flow"
import type { ApprovalRecord, ManagedMonthlyPlan } from "@/mobile/features/monthly-plan/types"
import { formatDateTime } from "@/utils/date"
const props=defineProps<{ managers?: { id: string; name: string }[]; plan?: ManagedMonthlyPlan | null; record?: ApprovalRecord | null; applicant?: string }>()
const nodes=computed(()=>buildApprovalFlow(props.plan || null,props.record || null,props.managers || [],props.applicant || ""))
const current=computed(()=>nodes.value.find(node=>node.state==='current') || nodes.value.at(-1))
</script>

<template>
  <aside class="dashboard-card approval-timeline" aria-labelledby="approval-timeline-title">
    <header class="flow-heading"><h2 id="approval-timeline-title">审批流程</h2><span v-if="current" class="flow-current">当前：{{current.title}}</span></header>
    <ol>
      <li v-for="node in nodes" :key="node.id" class="flow-item" :class="[`flow-item--${node.state}`, { 'flow-item--terminal': node.terminal }]" :aria-current="node.state==='current'?'step':undefined">
        <div v-if="node.terminal" class="flow-terminal">{{node.title}}</div>
        <div v-else class="flow-node">
          <div class="flow-node-heading"><h3>{{node.title}}</h3><span class="flow-result">{{node.result}}</span></div>
          <dl><div><dt>处理人</dt><dd>{{node.person}}</dd></div><div><dt>操作时间</dt><dd><time v-if="node.time" :datetime="node.time">{{formatDateTime(node.time)}}</time><span v-else>—</span></dd></div></dl>
          <div v-if="node.reason" class="flow-reason"><strong>{{node.state==='rejected'?'驳回原因':'审批意见'}}</strong><p class="user-content">{{node.reason}}</p></div>
        </div>
      </li>
    </ol>
  </aside>
</template>

<style scoped src="./ApprovalTimeline.css"></style>
