<script setup lang="ts">
import { computed, ref } from "vue"
import { RouterLink, useRoute, useRouter } from "vue-router"
import { ChevronLeft } from "lucide-vue-next"
import companyLogo from "@/assets/brand/dingchi-logo.png"
import { useAuthStore } from "@/features/auth/store"
import NoticeCenter from "@/mobile/components/feedback/NoticeCenter.vue"
import GlobalWatermark from "@/mobile/components/security/GlobalWatermark.vue"
import TodoFloatingWidget from "@/mobile/features/todos/components/TodoFloatingWidget.vue"
import UserProfileMenu from "./components/UserProfileMenu.vue"
const route = useRoute()
const router = useRouter()
const showBack = computed(() => !route.meta.public && !links.value.some(link => link.path === route.path))
function goBack() {
  if (route.name === "mobile-weekly-report-month-detail") {
    void router.push({ name: "mobile-weekly-reports", query: { tab: "monthly" } })
    return
  }
  const previous = router.options.history.state.back
  if (typeof previous === "string" && previous.startsWith("/mobile") && !previous.startsWith("/mobile/login")) { router.back(); return }
  const path = route.path.startsWith("/mobile/monthly-plans/") ? "/mobile/monthly-plans" : route.path.startsWith("/mobile/weekly-reports/") ? "/mobile/weekly-reports" : "/mobile"
  const query = typeof route.query.tab === "string" ? {tab: route.query.tab} : undefined
  void router.push({path,query})
}
const auth = useAuthStore()
const menuOpen = ref(false)
function isActive(path: string) {
  return route.path === path || (path !== "/mobile" && route.path.startsWith(`${path}/`))
}
const admin = computed(() => auth.roles.some(role => role.role_code === "system_admin"))
const links = computed(() => [
  { label: "总览", path: "/mobile" },
  { label: "月度计划", path: "/mobile/monthly-plans" },
  { label: "周报", path: "/mobile/weekly-reports" },
  { label: "AI 助手", path: "/mobile/ai-chat" },
  ...(admin.value ? [
    { label: "用户管理", path: "/mobile/users" },
    { label: "职位管理", path: "/mobile/roles" },
    { label: "系统设置", path: "/mobile/system-settings" },
  ] : []),
])
const watermark = computed(() => `${auth.user?.display_name || ""} · ${auth.roles.map(role => role.role_name).join(" / ")}`)
</script>
<template>
  <div class="mobile-shell">
    <template v-if="!route.meta.public">
      <header class="mobile-header">
        <div class="mobile-header-left"><button v-if="showBack" type="button" class="mobile-back-button" aria-label="返回" title="返回" @click="goBack"><ChevronLeft :size="22" :stroke-width="1.8" aria-hidden="true" /></button><RouterLink to="/mobile" class="mobile-brand"><img :src="companyLogo" alt="鼎驰公司 Logo" /><span>鼎驰周报</span></RouterLink></div>
        <div class="mobile-header-controls"><button v-if="admin" type="button" :aria-expanded="menuOpen" aria-controls="mobile-management-menu" @click="menuOpen = !menuOpen">{{ menuOpen ? "收起" : "管理" }}</button><UserProfileMenu /></div>
      </header>
      <nav v-if="menuOpen && admin" id="mobile-management-menu" class="mobile-menu" aria-label="主导航">
        <RouterLink v-for="link in links.slice(4)" :key="link.path" :to="link.path" @click="menuOpen = false">{{ link.label }}</RouterLink>
      </nav>
      <div class="mobile-action-bar"><div id="weekly-report-header-actions" class="mobile-actions" /></div>
    </template>
    <main class="mobile-main"><slot /></main>
    <nav v-if="!route.meta.public" class="mobile-bottom-nav" aria-label="快捷导航">
      <RouterLink v-for="link in links.slice(0, 4)" :key="link.path" :to="link.path" :class="{selected: isActive(link.path)}" :aria-current="isActive(link.path) ? 'page' : undefined">{{ link.label }}</RouterLink>
    </nav>
    <template v-if="!route.meta.public"><TodoFloatingWidget /><GlobalWatermark :text="watermark" /></template>
    <NoticeCenter />
  </div>
</template>
<style scoped src="./DefaultLayout.css"></style>
