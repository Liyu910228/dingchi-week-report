<script setup lang="ts">
import { computed, onMounted } from "vue"
import { RouterLink, useRoute } from "vue-router"

import dingchiLogo from "@/assets/brand/dingchi-logo.png"
import sidebarDataColumns from "@/assets/dashboard/hero-data-columns.png"
import NoticeCenter from "@/components/feedback/NoticeCenter.vue"
import BackButton from "@/components/navigation/BackButton.vue"
import TodoFloatingWidget from "@/features/todos/components/TodoFloatingWidget.vue"
import GlobalWatermark from "@/components/security/GlobalWatermark.vue"
import { useAuthStore } from "@/features/auth/store"
import { formatDateTime } from "@/utils/date"

import NavIcon from "./components/NavIcon.vue"
import UserProfileMenu from "./components/UserProfileMenu.vue"

const authStore = useAuthStore()
const route = useRoute()
const isPublic = computed(() => Boolean(route.meta.public))
const isDashboard = computed(() => route.path === "/")
const isSecondaryPage = computed(() => [
  "weekly-report-new",
  "weekly-report-edit",
  "weekly-report-detail",
  "weekly-report-month-detail",
  "monthly-plan-new",
  "monthly-plan-edit",
  "monthly-plan-detail",
  "monthly-plan-change-edit",
  "monthly-plan-change-detail",
  "monthly-plan-change-new",
].includes(String(route.name)))
const isSystemAdmin = computed(() => authStore.effectiveRole?.role_code === "system_admin")
const secondaryBackLocation = computed(() => {
  if (route.name === "weekly-report-month-detail") {
    return { name: "weekly-reports", query: { tab: "monthly" } }
  }
  if (String(route.name).startsWith("monthly-plan")) {
    const tab = route.query.tab
    return {
      name: "monthly-plans",
      query: typeof tab === "string" ? { tab } : undefined,
    }
  }
  const query: Record<string, string | string[]> = {}
  for (const key of ["tab", "month_key", "period_start", "period_end", "group_id", "employee_id", "filter_role_code", "page"]) {
    const value = route.query[key]
    if (typeof value === "string") query[key] = value
    else if (Array.isArray(value)) query[key] = value.filter((item): item is string => item !== null)
  }
  return { name: "weekly-reports", query }
})
const watermarkText = computed(() => {
  const user = authStore.user
  if (!user) return ""
  return `${user.display_name || user.username} · ${authStore.roles.map(role => role.role_name).join("、") || "暂无职位"}`
})
const headerDate = formatDateTime(new Date())
// 不同数据范围仍由当前角色和路由权限控制，导航统一使用"周报"作为用户可见名称。
const weeklyReportLabel = "周报"

type NavItem = {
  label: string
  to: string
  icon: "home" | "report" | "users" | "roles" | "sparkles" | "settings"
  visible: boolean
}

const navItems = computed<NavItem[]>(() => [
  { label: "总览", to: "/", icon: "home", visible: true },
  { label: "月度计划", to: "/monthly-plans", icon: "report", visible: true },
  { label: weeklyReportLabel, to: "/weekly-reports", icon: "report", visible: true },
  {
    label: "用户管理",
    to: "/users",
    icon: "users",
    visible: isSystemAdmin.value,
  },
  {
    label: "职位管理",
    to: "/roles",
    icon: "roles",
    visible: isSystemAdmin.value,
  },
  {
    label: "系统设置",
    to: "/system-settings",
    icon: "settings",
    visible: isSystemAdmin.value,
  },
  { label: "AI 助手", to: "/ai-chat", icon: "sparkles", visible: true },
])

const visibleNavItems = computed(() => navItems.value.filter((item) => item.visible))

onMounted(() => {
  if (!isPublic.value) {
    void authStore.bootstrap()
  }
})

</script>

<template>
  <template v-if="isPublic">
    <slot />
  </template>
  <div v-else class="app-shell">
    <aside class="app-sidebar">
      <RouterLink class="brand" to="/" aria-label="返回总览">
        <span class="brand-mark">
          <img :src="dingchiLogo" alt="鼎驰" />
        </span>
        <span class="brand-name">鼎驰周报</span>
      </RouterLink>
      <nav class="side-nav" aria-label="主导航">
        <RouterLink
          v-for="item in visibleNavItems"
          :key="item.label"
          :to="item.to"
          :class="{ 'router-link-active': route.matched.some((record) => record.path === item.to) }"
        >
          <NavIcon :name="item.icon" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
      <div class="sidebar-lower">
        <img class="sidebar-data-art" :src="sidebarDataColumns" alt="" aria-hidden="true" />
        <UserProfileMenu />
      </div>
    </aside>

    <section class="app-content">
      <header v-if="!isDashboard" class="app-header">
        <div v-if="isSecondaryPage" class="header-back">
          <BackButton :to="secondaryBackLocation" />
        </div>
        <div class="header-context">
          <span class="header-kicker">智能周报驾驶舱</span>
          <span class="header-date">本周 {{ headerDate }}</span>
        </div>
        <div id="weekly-report-header-actions" class="header-actions" />
      </header>
      <main class="app-main" :class="{ 'app-main--dashboard': isDashboard }">
        <slot />
      </main>
    </section>
    <TodoFloatingWidget />
    <NoticeCenter />
    <GlobalWatermark :text="watermarkText" />
  </div>
</template>

<style scoped src="./DefaultLayout.css"></style>
