import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router"

import { setReportRole } from "@/shared/api/report-context"

import { useAuthStore } from "@/features/auth/store"

import { mobileRoutes } from "./mobile"
import { isMobileDevice, mobilePath } from "@/shared/utils/device-routing"

const routes: RouteRecordRaw[] = [
  {path:"/monthly-plans/:planId/change",name:"monthly-plan-change-new",component:()=>import("@/views/monthly-plan/EditView.vue"),meta:{title:"填写月度计划变更",requiresAuth:true}},
  { path: "/reporting-position", name: "reporting-position", redirect: to => ({name:to.query.target === "monthly-plan-new"?"monthly-plan-new":"weekly-report-new"}) },
  {path:"/monthly-plans/changes/:changeId/edit",name:"monthly-plan-change-edit",component:()=>import("@/views/monthly-plan/EditView.vue"),meta:{title:"填写月度计划变更",requiresAuth:true}},
  {path:"/monthly-plans/changes/:changeId",name:"monthly-plan-change-detail",component:()=>import("@/views/monthly-plan/ChangeDetailView.vue"),meta:{title:"月度计划变更",requiresAuth:true}},
  {
    path: "/",
    name: "dashboard",
    component: () => import("@/views/dashboard/IndexView.vue"),
    meta: { title: "周报总览", requiresAuth: true },
  },
  {
    path: "/login",
    name: "login",
    component: () => import("@/views/login/IndexView.vue"),
    meta: { title: "登录", public: true },
  },
  {
    path: "/monthly-plans", name: "monthly-plans",
    component: () => import("@/views/monthly-plan/IndexView.vue"),
    meta: {title: "月度计划", requiresAuth: true},
  },
  {
    path: "/monthly-plans/new", name: "monthly-plan-new",
    component: () => import("@/views/monthly-plan/EditView.vue"),
    meta: {title: "填写月度计划", requiresAuth: true},
  },
  {
    path: "/monthly-plans/:planId/edit", name: "monthly-plan-edit",
    component: () => import("@/views/monthly-plan/EditView.vue"),
    meta: {title: "修改月度计划", requiresAuth: true},
  },
  {
    path: "/monthly-plans/:planId", name: "monthly-plan-detail",
    component: () => import("@/views/monthly-plan/DetailView.vue"),
    meta: {title: "月度计划详情", requiresAuth: true},
  },
  {
    path: "/weekly-reports",
    name: "weekly-reports",
    component: () => import("@/views/weekly-report/IndexView.vue"),
    meta: { title: "我的周报", requiresAuth: true },
  },
  {
    path: "/weekly-reports/new",
    name: "weekly-report-new",
    component: () => import("@/views/weekly-report/TemplateEditorView.vue"),
    meta: { title: "填写周报", requiresAuth: true },
  },
  {
    path: "/weekly-reports/:reportId/edit",
    name: "weekly-report-edit",
    component: () => import("@/views/weekly-report/TemplateEditorView.vue"),
    meta: { title: "编辑周报", requiresAuth: true },
  },
  {
    path: "/weekly-reports/:reportId",
    name: "weekly-report-detail",
    component: () => import("@/views/weekly-report/DetailView.vue"),
    meta: { title: "周报详情", requiresAuth: true },
  },
  {
    path: "/users",
    name: "users",
    component: () => import("@/views/users/IndexView.vue"),
    meta: { title: "用户管理", requiresAuth: true, adminOnly: true },
  },
  {
    path: "/roles",
    name: "roles",
    component: () => import("@/views/roles/IndexView.vue"),
    meta: { title: "职位管理", requiresAuth: true, adminOnly: true },
  },
  {
    path: "/customers",
    name: "customers",
    redirect: { name: "system-settings-customers" },
  },
  {
    path: "/system-settings",
    component: () => import("@/views/system-settings/IndexView.vue"),
    meta: { title: "系统设置", requiresAuth: true, adminOnly: true },
    children: [
      { path: "", name: "system-settings", redirect: { name: "system-settings-customers" } },
      {
        path: "customers",
        name: "system-settings-customers",
        component: () => import("@/views/system-settings/CustomerManagementView.vue"),
        meta: { title: "系统设置 - 客户管理" },
      },
      {
        path: "models",
        name: "system-settings-models",
        component: () => import("@/views/system-settings/ModelConfigurationView.vue"),
        meta: { title: "系统设置 - 模型配置" },
      },
    ],
  },
  {
    path: "/ai-chat",
    name: "ai-chat",
    component: () => import("@/views/chat/IndexView.vue"),
    meta: { title: "AI 助手", requiresAuth: true },
  },
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    component: () => import("@/views/not-found/IndexView.vue"),
    meta: { title: "页面不存在" },
  },
]

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [...mobileRoutes, ...routes],
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  const mobile = to.path === "/mobile" || to.path.startsWith("/mobile/")
  if (!mobile && isMobileDevice()) return { path: mobilePath(to.path), query: to.query, hash: to.hash, replace: true }
  const home = mobile ? "mobile-dashboard" : "dashboard"
  const login = mobile ? "mobile-login" : "login"
  const authStore = useAuthStore()
  if (to.meta.public) {
    if (to.name === login && authStore.isAuthenticated) return { name: home }
    return true
  }
  await authStore.bootstrap()
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return { name: login, query: { redirect: to.fullPath } }
  }
  if (to.meta.adminOnly && authStore.effectiveRole?.role_code !== "system_admin") {
    return { name: home }
  }
  setReportRole("")
  return true
})

router.afterEach((to) => {
  const appTitle = import.meta.env.VITE_APP_TITLE || "鼎驰周报"
  document.title = to.meta.title ? String(to.meta.title) + " | " + appTitle : appTitle
})
