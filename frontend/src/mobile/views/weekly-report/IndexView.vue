<script setup lang="ts">
import { computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import ScrollableTabs from "@/mobile/components/navigation/ScrollableTabs.vue"
import SharedReportsSection from "./components/SharedReportsSection.vue"

import { useAuthStore } from "@/features/auth/store"

import AllReportsView from "./all/IndexView.vue"
import SelfReportsView from "./self/IndexView.vue"
import TeamReportsView from "./team/IndexView.vue"

const authStore = useAuthStore()
const route = useRoute(), router = useRouter()
const hasTeam = computed(() => authStore.effectiveRole?.scope === "team" || (authStore.effectiveRole?.scope === "all" && authStore.reportingRoles.length > 0))
const allOnly = computed(() => authStore.effectiveRole?.scope === "all" && !authStore.reportingRoles.length)
const sharedTab = computed({
 get: () => route.query.tab === "shared" ? "shared" : hasTeam.value && route.query.tab === "team" ? "team" : allOnly.value ? "all" : "self",
 set: (tab:string) => { void router.replace({query:{...route.query,tab,employee_id:undefined,group_id:undefined,page:undefined}}) },
})
const tabs = computed(() => [
 {id:allOnly.value ? "all" : "self",name:allOnly.value ? "全员周报" : "我的周报"},
 ...(hasTeam.value ? [{id:"team",name:"团队周报"}] : []),
 {id:"shared",name:"共享周报"},
])
const reportPage = computed(() => {
  const scope = authStore.effectiveRole?.scope
  if (scope === "all") return authStore.reportingRoles.length ? TeamReportsView : AllReportsView
  if (scope === "team") return TeamReportsView
  return SelfReportsView
})
</script>

<template>
  <div v-if="authStore.isAuthenticated" class="dashboard-card weekly-workspace">
    <div class="weekly-workspace-tabs"><ScrollableTabs v-model="sharedTab" :items="tabs" /><div id="weekly-list-create-action" class="weekly-list-create-action" /></div>
    <SharedReportsSection v-if="sharedTab==='shared'" :key="authStore.user?.id" />
    <component v-else :is="reportPage" />
  </div>
</template>

<style scoped src="./IndexView.css"></style>

