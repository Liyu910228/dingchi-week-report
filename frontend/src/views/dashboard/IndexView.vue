<script setup lang="ts">
import { computed, defineAsyncComponent } from "vue"

import { useAuthStore } from "@/features/auth/store"

const authStore = useAuthStore()
// 首页按数据范围解析版本：个人、团队、领导版分别维护，其他范围使用兼容入口。
// 新增首页版本时只在对应目录增加入口，不把不同版本的页面逻辑混在这里。
const isPersonal = computed(() => authStore.effectiveRole?.scope === "self")
const isTeam = computed(() => authStore.effectiveRole?.scope === "team")
const isLeader = computed(() => authStore.effectiveRole?.scope === "all")
const PersonalHomeV1 = defineAsyncComponent(() => import("./personal/v1/IndexView.vue"))
const TeamHomeV1 = defineAsyncComponent(() => import("./team/v1/IndexView.vue"))
const LeaderHomeV1 = defineAsyncComponent(() => import("./leader/v1/IndexView.vue"))
const ScopedDashboardV1 = defineAsyncComponent(() => import("./legacy/IndexView.vue"))
</script>

<template>
    <PersonalHomeV1 v-if="isPersonal" />
    <TeamHomeV1 v-else-if="isTeam" />
    <LeaderHomeV1 v-else-if="isLeader" />
    <ScopedDashboardV1 v-else />
</template>
