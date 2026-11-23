import type { RouteRecordRaw } from "vue-router"

export const mobileRoutes: RouteRecordRaw[] = [
  {path:"/mobile/weekly-reports/monthly/:employeeId/:monthKey",name:"mobile-weekly-report-month-detail",component:()=>import("@/mobile/views/weekly-report/MonthDetailView.vue"),meta:{title:"月度周报",requiresAuth:true,mobile:true}},
  {path:"/mobile/monthly-plans/:planId/change",name:"mobile-monthly-plan-change-new",component:()=>import("@/mobile/views/monthly-plan/EditView.vue"),meta:{mobile:true,title:"填写月度计划变更",requiresAuth:true}},
  { path: "/mobile/reporting-position", name: "mobile-reporting-position", redirect: to => ({name:to.query.target === "mobile-monthly-plan-new"?"mobile-monthly-plan-new":"mobile-weekly-report-new"}) },
  {path:"/mobile/monthly-plans/changes/:changeId/edit",name:"mobile-monthly-plan-change-edit",component:()=>import("@/mobile/views/monthly-plan/EditView.vue"),meta:{mobile:true,title:"填写月度计划变更",requiresAuth:true}},
  {path:"/mobile/monthly-plans/changes/:changeId",name:"mobile-monthly-plan-change-detail",component:()=>import("@/mobile/views/monthly-plan/ChangeDetailView.vue"),meta:{mobile:true,title:"月度计划变更",requiresAuth:true}},
  {
    path: "/mobile",
    name: "mobile-dashboard",
    component: () => import("@/mobile/views/dashboard/IndexView.vue"),
    meta: { mobile: true, title: "周报总览", requiresAuth: true },
  },
  {
    path: "/mobile/login",
    name: "mobile-login",
    component: () => import("@/mobile/views/login/IndexView.vue"),
    meta: { mobile: true, title: "登录", public: true },
  },
  {
    path: "/mobile/monthly-plans", name: "mobile-monthly-plans",
    component: () => import("@/mobile/views/monthly-plan/IndexView.vue"),
    meta: { mobile: true,title: "月度计划", requiresAuth: true},
  },
  {
    path: "/mobile/monthly-plans/new", name: "mobile-monthly-plan-new",
    component: () => import("@/mobile/views/monthly-plan/EditView.vue"),
    meta: { mobile: true,title: "填写月度计划", requiresAuth: true},
  },
  {
    path: "/mobile/monthly-plans/:planId/edit", name: "mobile-monthly-plan-edit",
    component: () => import("@/mobile/views/monthly-plan/EditView.vue"),
    meta: { mobile: true,title: "修改月度计划", requiresAuth: true},
  },
  {
    path: "/mobile/monthly-plans/:planId", name: "mobile-monthly-plan-detail",
    component: () => import("@/mobile/views/monthly-plan/DetailView.vue"),
    meta: { mobile: true,title: "月度计划详情", requiresAuth: true},
  },
  {
    path: "/mobile/weekly-reports",
    name: "mobile-weekly-reports",
    component: () => import("@/mobile/views/weekly-report/IndexView.vue"),
    meta: { mobile: true, title: "我的周报", requiresAuth: true },
  },
  {
    path: "/mobile/weekly-reports/new",
    name: "mobile-weekly-report-new",
    component: () => import("@/mobile/views/weekly-report/TemplateEditorView.vue"),
    meta: { mobile: true, title: "填写周报", requiresAuth: true },
  },
  {
    path: "/mobile/weekly-reports/:reportId/edit",
    name: "mobile-weekly-report-edit",
    component: () => import("@/mobile/views/weekly-report/TemplateEditorView.vue"),
    meta: { mobile: true, title: "编辑周报", requiresAuth: true },
  },
  {
    path: "/mobile/weekly-reports/:reportId",
    name: "mobile-weekly-report-detail",
    component: () => import("@/mobile/views/weekly-report/DetailView.vue"),
    meta: { mobile: true, title: "周报详情", requiresAuth: true },
  },
  {
    path: "/mobile/users",
    name: "mobile-users",
    component: () => import("@/mobile/views/users/IndexView.vue"),
    meta: { mobile: true, title: "用户管理", requiresAuth: true, adminOnly: true },
  },
  {
    path: "/mobile/roles",
    name: "mobile-roles",
    component: () => import("@/mobile/views/roles/IndexView.vue"),
    meta: { mobile: true, title: "职位管理", requiresAuth: true, adminOnly: true },
  },
  {
    path: "/mobile/customers",
    name: "mobile-customers",
    redirect: { name: "mobile-system-settings-customers" },
  },
  {
    path: "/mobile/system-settings",
    component: () => import("@/mobile/views/system-settings/IndexView.vue"),
    meta: { mobile: true, title: "系统设置", requiresAuth: true, adminOnly: true },
    children: [
      { path: "", name: "mobile-system-settings", redirect: { name: "mobile-system-settings-customers" } },
      {
        path: "customers",
        name: "mobile-system-settings-customers",
        component: () => import("@/mobile/views/system-settings/CustomerManagementView.vue"),
        meta: { mobile: true, title: "系统设置 - 客户管理" },
      },
      {
        path: "models",
        name: "mobile-system-settings-models",
        component: () => import("@/views/system-settings/ModelConfigurationView.vue"),
        meta: { mobile: true, title: "系统设置 - 模型配置" },
      },
    ],
  },
  {
    path: "/mobile/ai-chat",
    name: "mobile-ai-chat",
    component: () => import("@/mobile/views/chat/IndexView.vue"),
    meta: { mobile: true, title: "AI 助手", requiresAuth: true },
  },
  {
    path: "/mobile/:pathMatch(.*)*",
    name: "mobile-not-found",
    component: () => import("@/mobile/views/not-found/IndexView.vue"),
    meta: { mobile: true, title: "页面不存在" },
  },
]
