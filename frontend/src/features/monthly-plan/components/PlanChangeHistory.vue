<script setup lang="ts">
import SubmissionSnapshotTabs from "@/features/submissions/components/SubmissionSnapshotTabs.vue"
import { computed } from "vue"
import type { ApprovedPlanVersion } from "@/features/monthly-plan/types"
import MonthlyPlanTaskPanel from "@/features/monthly-plan/components/MonthlyPlanTaskPanel.vue"
import { formatDateTime } from "@/utils/date"
const props=defineProps<{history:ApprovedPlanVersion[]}>()
const entries=computed(()=>[...props.history].sort((a,b)=>Date.parse(b.created_at)-Date.parse(a.created_at) || b.id.localeCompare(a.id,'en',{numeric:true})))
function positionLabel(entry:ApprovedPlanVersion){
 const names=entry.snapshot.parts?.map(part=>part.role_name || part.role_code).filter(Boolean)
 return names?.length ? [...new Set(names)].join(" / ") : entry.snapshot.role_name || entry.role_name || entry.snapshot.role_code || entry.role_code || "—"
}
</script>
<template>
<section v-if="history.length" class="dashboard-card change-history"><h2>变更历史</h2>
 <details v-for="entry in entries" :key="entry.id"><summary><strong>{{entry.process_type==='initial'?'申请':'变更'}}</strong><span class="history-position">{{positionLabel(entry)}}</span><time :datetime="entry.created_at">{{formatDateTime(entry.created_at)}}</time></summary>
 <div class="version-content"><h3>月度目标</h3><p>{{entry.snapshot.summary}}</p><SubmissionSnapshotTabs v-if="entry.snapshot.parts" :snapshot="entry.snapshot" /><MonthlyPlanTaskPanel v-else :tasks="entry.snapshot.tasks" :month-key="entry.snapshot.month_key" :template-code="entry.snapshot.template_code" readonly /></div>
 </details>
</section>
</template>
<style scoped src="./PlanChangeHistory.css"></style>
