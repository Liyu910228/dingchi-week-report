# Frontend

Vue 3 + Vite 6 的 TypeScript 前端。

页面与模块开发必须遵守 [前端页面开发约束规范](docs/frontend-development-conventions.md)。
前后端接口还必须遵守仓库级 [API 对接规范](../docs/frontend-backend-api-conventions.md)。

## 结构

```text
src/
├─ app/                 # 路由、全局 Pinia 注册和应用级状态
├─ assets/              # 图片、字体等静态资源（不放全局 CSS）
│  ├─ brand/             # 品牌 Logo 等资源
│  └─ dashboard/         # 驾驶舱分层装饰切片与 KPI 图标精灵
├─ components/          # 跨多个业务复用的全局基础组件，按功能分类
│  └─ feedback/         # 提示、加载、空状态等反馈组件
├─ features/            # 按功能聚合 API、状态和领域类型
│  ├─ auth/              # 登录、Bearer 会话和角色切换
│  ├─ dashboard/         # 驾驶舱聚合数据
│  ├─ directory/         # 用户、角色、分组管理
│  ├─ weekly-report/     # 周报模板、周期状态和附件
│  └─ chat/
├─ layouts/             # 页面布局
├─ shared/api/          # Axios 实例、统一响应、错误处理和安全接口
├─ shared/security/     # RSA-OAEP-SHA256 浏览器加密工具
├─ styles/              # 全局样式入口、主题变量、重置和基础类
├─ utils/               # 无业务语义的全局纯工具函数
└─ views/               # 按功能模块组织的路由页面
   ├─ chat/
   │  ├─ IndexView.vue
   │  └─ components/
   ├─ dashboard/
   │  ├─ IndexView.vue
   │  └─ components/
   ├─ weekly-report/
   │  ├─ IndexView.vue
   │  ├─ TemplateEditorView.vue
   │  ├─ EditView.vue
   │  ├─ DetailView.vue
   │  ├─ templates/       # 按 template_code/{version} 隔离的专用页面
   │  └─ components/
   ├─ users/
   │  └─ IndexView.vue
   ├─ roles/
   │  └─ IndexView.vue
   └─ not-found/
      └─ IndexView.vue
```

每个路由功能都建立独立目录，并以 `IndexView.vue` 作为主入口。模块私有组件放在其
`components/` 下；新增子页面时在同一模块目录创建独立的 `*View.vue`，不要继续堆入入口页面。
跨页面复用的业务状态、请求和类型放在 `features/`；HTTP 客户端、通用类型等共享基础设施
放在 `shared/`。

跨业务复用的按钮、弹窗、分页等基础 UI 按功能分类放在 `components/<category>/`，禁止
把组件直接平铺在 `components/` 根目录。例如提示反馈放 `components/feedback/`，弹窗
放 `components/overlay/`，分页放 `components/navigation/`。无业务语义的纯函数放在
`utils/`。全局 CSS 只从 `styles/index.css` 导入，主题变量、重置和全局基础类分别放在
`tokens.css`、`reset.css` 和 `global.css`。

页面或组件存在私有样式时，使用同目录、同名 CSS 文件一对一关联：

```vue
<style scoped src="./ChatComposer.css"></style>
```

没有私有样式的 Vue 文件不创建空 CSS；业务页面选择器不得写入全局样式。

接口基地址通过 `VITE_API_BASE_URL` 配置，默认 `/api`；业务模块只填写 `/v1/...` 路径。
所有请求会由 `shared/api/http.ts` 自动附加 `X-Trace-ID`。页面密码必须调用
`shared/security/password.ts` 的 `encryptPassword()`，不能把私钥或服务端秘密放入
`VITE_*` 环境变量。

## 命令

```powershell
npm install
npm run dev
npm run type-check
npm run build
npm run preview
```

## 已实现页面

- `/login`：RSA-OAEP-SHA256 密码传输登录，支持本地演示账号。
- `/`：蓝白风格周报驾驶舱，趋势图和环形图使用 ECharts Canvas 渲染。
- `/weekly-reports`、`/weekly-reports/new`：周报列表和模板编码驱动的填写；招聘专员与招聘经理共同绑定 `recruitment_v1`，页面入口位于 `views/weekly-report/templates/recruitment/v1/`。
- `/weekly-reports/:id`：公共详情页，按周报保存的 `template_code` 展示任务字段。
- `/users`、`/roles`：用户上下级/分组、角色和模板范围管理。
