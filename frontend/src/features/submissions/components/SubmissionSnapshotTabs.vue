<script setup lang="ts">
import {computed,ref,watch} from "vue"
import ScrollableTabs from "@/components/navigation/ScrollableTabs.vue"
import PlanComparison from "@/features/monthly-plan/components/PlanComparison.vue"
import type {PlanSnapshot} from "@/features/monthly-plan/types"
import {monthlyBodies} from "../template-registry"
const props=defineProps<{snapshot:PlanSnapshot;baseline?:PlanSnapshot|null;collapseFull?:boolean}>()
const active=ref("")
const expanded=ref(false)
watch(()=>[props.snapshot,active.value],()=>{expanded.value=false})
const tabs=computed(()=>(props.snapshot.parts || []).map(p=>({id:p.role_code,name:p.role_name})))
watch(tabs,value=>{if(!value.some(p=>p.id===active.value))active.value=value[0]?.id || ""},{immediate:true})
</script>
<template>
 <div class="snapshot-tabs">
  <ScrollableTabs v-model="active" :items="tabs" />
  <section v-for="part in snapshot.parts" :key="part.role_code" v-show="active===part.role_code" class="snapshot-pane">
   <PlanComparison v-if="baseline?.parts?.some(p=>p.role_code===part.role_code)" :before="{...baseline.parts.find(p=>p.role_code===part.role_code)!.payload,month_key:snapshot.month_key,template_code:part.template_code}" :after="{...part.payload,month_key:snapshot.month_key,template_code:part.template_code}" />
   <div v-if="collapseFull && baseline" class="snapshot-expand-action"><button type="button" class="ghost-button" :aria-expanded="expanded" :aria-controls="`complete-application-${part.role_code}`" @click="expanded=!expanded">{{expanded?'收起完整申请内容':'查看完整申请内容'}}</button></div>
   <section v-if="!collapseFull || !baseline || (expanded && active===part.role_code)" :id="collapseFull && baseline ? `complete-application-${part.role_code}` : undefined" class="snapshot-complete" :class="{'snapshot-complete--expanded':collapseFull && baseline}">
    <h3 v-if="collapseFull && baseline">本次变更申请完整内容</h3>
    <component :is="monthlyBodies[part.template_code]" :part="part" :month-key="snapshot.month_key" readonly />
   </section>
  </section>
 </div>
</template>
<style scoped src="./SubmissionSnapshotTabs.css"></style>
