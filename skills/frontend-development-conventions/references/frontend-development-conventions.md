# 前端页面开发约束规范

状态：强制执行  
适用范围：frontend/src 下所有新增、重构的页面与前端业务代码  
技术栈：Vue 3、TypeScript、Vue Router、Pinia、Axios、Vite 6

本文中的“必须”“禁止”为强制规则；“建议”为默认做法。如确有例外，必须在代码评审说明中写明原因，不能静默绕过规范。

## 1. 核心目标

1. 页面按功能模块组织，不在 views 根目录平铺页面。
2. 路由入口页面只负责页面编排，不承载大段 UI 和复杂业务逻辑。
3. 页面组件、领域逻辑和通用能力分层存放，保持单向依赖。
4. 一个文件只承担一个清晰职责，避免超长组件和隐式耦合。
5. 所有后端请求、状态管理、环境变量和路由写法保持一致。
6. 界面只呈现必要、单一语言的用户文案，并保持紧凑、清晰的信息密度。

## 2. 标准目录结构

~~~text
src/
├─ app/
│  ├─ router/                     # 路由注册、守卫、路由元信息
│  └─ stores/                     # 应用级全局状态和 Pinia 注册
├─ assets/                        # 图片、字体等静态资源，不放全局 CSS
├─ components/                    # 跨业务、无业务语义的全局基础组件
│  └─ <category>/                 # 按组件功能分类，禁止在根目录平铺组件
├─ features/
│  └─ <domain>/
│     ├─ api.ts                   # 领域接口
│     ├─ store.ts                 # 领域 Pinia 状态
│     ├─ types.ts                 # 领域类型
│     ├─ components/              # 跨页面复用的领域组件（按需）
│     └─ composables/             # 跨页面复用的领域逻辑（按需）
├─ layouts/                       # 应用级页面布局
├─ shared/
│  ├─ api/                        # HTTP 客户端、统一响应和错误
│  ├─ composables/                # 通用组合式函数（按需）
│  ├─ constants/                  # 通用常量（按需）
│  └─ types/                      # 通用类型（按需）
├─ styles/
│  ├─ index.css                   # 全局样式唯一入口
│  ├─ tokens.css                  # 主题变量和设计令牌
│  ├─ reset.css                   # 浏览器默认样式重置
│  └─ global.css                  # 真正跨页面的基础类
├─ utils/                         # 无业务语义的全局纯工具函数
└─ views/
   └─ <module>/
      ├─ IndexView.vue            # 模块主入口页面
      ├─ DetailView.vue           # 独立子页面（按需）
      ├─ EditView.vue             # 独立子页面（按需）
      ├─ components/              # 仅供本页面模块使用的组件
      └─ composables/             # 仅供本页面模块使用的逻辑（按需）
~~~

禁止为了“看起来完整”创建空目录；只有出现对应代码时才创建可选目录。

## 3. 分层职责与依赖方向

总体依赖方向：

~~~text
app / layouts / views  →  features / components  →  shared / utils
~~~

| 层级 | 负责内容 | 可以依赖 | 禁止依赖 |
| --- | --- | --- | --- |
| app | 应用装配、路由、全局 UI/系统状态 | layouts、views、features、components、shared、utils | 在此堆放具体页面业务 |
| layouts | 全局导航、页头、页脚、页面框架 | app、features、components、shared、utils | views 下的模块私有组件 |
| views | 路由页面、页面级生命周期、页面组件编排 | 本模块、features、components、shared、utils | 其他模块的私有 components |
| features | 领域 API、状态、类型、跨页面领域逻辑 | 本领域、components、shared、utils | app、layouts、views |
| components | 跨业务基础 UI 组件 | shared、utils、第三方 UI 库 | app、layouts、views、features 的业务实现 |
| shared | HTTP、通用 composable、常量和类型等共享基础设施 | shared 内部、utils、第三方库 | app、layouts、views、features |
| utils | 无状态、无业务语义的纯工具函数 | utils 内部、第三方工具库 | app、layouts、views、features、components |

必须保持上述单向依赖，禁止通过相对路径或重新导出绕过依赖方向。

## 4. views 模块约束

### 4.1 模块目录

- 每个功能模块必须建立独立目录：views/<module>/。
- 模块目录必须使用 kebab-case，例如 weekly-report、employee-summary。
- views 根目录禁止新增 HomeView.vue、ReportView.vue 这类平铺文件。
- 每个模块必须有且只能有一个 IndexView.vue，作为模块默认主入口。
- 每个独立路由子页面必须创建单独文件，例如 DetailView.vue、CreateView.vue、EditView.vue。
- 只有本模块使用的组件必须放在 views/<module>/components/。
- 只有本模块使用的组合逻辑必须放在 views/<module>/composables/。

### 4.2 IndexView.vue 的职责

IndexView.vue 只能负责：

1. 组合模块内的页面组件。
2. 获取路由参数和查询参数。
3. 调用页面级 composable 或 feature store。
4. 执行页面级生命周期。
5. 处理少量页面级事件协调。

IndexView.vue 禁止：

1. 直接调用 Axios 或 shared/api/http。
2. 编写大段表单、表格、弹窗、列表项等具体 UI。
3. 放置可复用的数据转换或校验逻辑。
4. 同时管理两个及以上相互独立的业务流程。
5. 把所有子页面通过条件判断塞进同一个入口文件。

标准入口示例：

~~~vue
<script setup lang="ts">
import { onMounted } from "vue"

import { useWeeklyReportStore } from "@/features/weekly-report/store"

import ReportFilter from "./components/ReportFilter.vue"
import ReportList from "./components/ReportList.vue"

const reportStore = useWeeklyReportStore()

onMounted(() => {
  void reportStore.fetchList()
})
</script>

<template>
  <div class="page-stack">
    <ReportFilter
      :filters="reportStore.filters"
      @search="reportStore.fetchList"
    />
    <ReportList
      :items="reportStore.items"
      :loading="reportStore.isLoading"
    />
  </div>
</template>
~~~

## 5. 文件拆分规则

满足以下任一条件时必须拆分，不能继续向原文件追加代码：

1. IndexView.vue 超过 120 行。
2. 普通 Vue 单文件组件超过 250 行。
3. 单个函数超过 50 行。
4. 模板中出现两个及以上可独立命名的 UI 区块。
5. 同一文件同时包含筛选区、数据列表、编辑表单、弹窗中的两个及以上部分。
6. 同一 script 同时管理两个及以上独立请求流程。
7. 同一段模板或逻辑出现第二次，或预期会在其他页面复用。
8. 子页面依赖大量 v-if 切换才能与主页面共存。

拆分时按职责命名，不使用 Content.vue、Block.vue、Part.vue、Component1.vue 等无语义名称。

## 6. 组件放置决策

| 使用范围 | 放置位置 | 示例 |
| --- | --- | --- |
| 仅一个页面模块使用 | views/<module>/components/ | ChatComposer.vue |
| 同一领域的多个路由页面复用 | features/<domain>/components/ | WeeklyReportStatus.vue |
| 跨领域、无业务语义 | components/<category>/ | actions/BaseButton.vue、overlay/BaseDialog.vue、navigation/PaginationBar.vue |
| 完整路由页面 | views/<module>/*View.vue | DetailView.vue |

禁止从一个 views 模块导入另一个 views 模块的 components。需要跨模块复用时，必须先提升到对应 features 或全局 components 层。

### 6.1 全局组件分类

- components 根目录只保留说明文档等管理文件，禁止直接放置 `.vue` 组件及其私有 CSS。
- 全局组件必须放入 `components/<category>/`，分类目录使用 kebab-case。
- 推荐分类包括：actions、feedback、form、navigation、overlay、data-display 和 layout。
- 不属于现有分类时允许新增语义明确的分类，禁止使用 common、misc、other 等模糊名称。
- 禁止为了补齐推荐分类创建空目录；只有出现实际组件时才创建。
- 组件保持 PascalCase 命名，私有 CSS 与组件同名并放在同一分类目录。

### 6.2 容器组件与展示组件

- IndexView.vue 或模块容器组件可以读取 Pinia store、路由和 composable。
- 叶子展示组件默认只通过 props 接收数据，通过 emits 上报事件。
- 叶子组件禁止为了方便直接读取多个全局 store。
- 数据通过 props 向下流动，事件通过 emits 向上通知。
- 双向表单值使用 defineModel；业务动作仍使用显式事件。

## 7. 命名规范

| 对象 | 规则 | 示例 |
| --- | --- | --- |
| 模块目录 | kebab-case | weekly-report |
| 路由入口 | 固定为 IndexView.vue | views/chat/IndexView.vue |
| 路由子页面 | PascalCase + View | DetailView.vue |
| Vue 组件 | PascalCase，名称表达职责 | ChatMessageList.vue |
| 组合式函数 | use + PascalCase | useReportFilters.ts |
| Pinia Store | use + PascalCase + Store | useChatStore |
| API 函数 | 动词开头 | getReportList、createReport |
| 布尔变量 | is、has、can、should 开头 | isLoading、hasMessages |
| 事件 | 模板中使用 kebab-case | check-backend、update-filter |

禁止含义模糊的缩写，业务名词必须在目录、类型、接口和组件之间保持一致。

## 8. 状态管理规范

按以下优先级选择状态位置：

1. 只影响单个组件：使用 ref、reactive 或 computed。
2. 同一页面模块多个组件共享：放到页面容器或 views/<module>/composables/。
3. 同一领域多个页面共享：放到 features/<domain>/store.ts。
4. 全应用共享的主题、会话、系统状态：放到 app/stores/。

禁止：

- 把页面临时状态放入应用级 Store。
- 在 Store 中操作 DOM。
- 在展示组件中复制一份与 Store 含义相同的长期状态。
- 在多个 Store 之间形成循环调用。

异步 action 必须统一维护 loading 和 error，并通过 try/finally 恢复 loading 状态。

## 9. API 调用规范

- 所有 HTTP 请求必须通过 shared/api/http.ts 导出的 request 方法。
- 禁止在页面或组件中直接 import axios。
- VITE_API_BASE_URL 固定承载 /api 前缀，业务接口只填写 /v1/...。
- 禁止硬编码后端域名、端口和完整 URL。
- 每个领域的接口必须放在 features/<domain>/api.ts。
- 请求参数、响应结果和页面模型必须有明确 TypeScript 类型。
- 错误文案统一通过 shared/api/errors.ts 处理，不在每个组件重复解析 AxiosError。
- 页面组件不得依赖后端原始响应包络，应由 request 方法返回 data。

正确示例：

~~~ts
export function getWeeklyReports(): Promise<WeeklyReport[]> {
  return request<WeeklyReport[]>({
    method: "GET",
    url: "/v1/weekly-reports/",
  })
}
~~~

错误示例：

~~~ts
axios.get("http://127.0.0.1:8000/api/v1/weekly-reports/")
~~~

## 10. 路由规范

- 路由统一维护在 app/router/ 下。
- 路由页面必须懒加载。
- path 和 name 使用 kebab-case。
- 每个页面必须配置 meta.title。
- 模块默认路由必须指向 views/<module>/IndexView.vue。
- 模块子路由必须指向同目录下独立的 *View.vue。
- 404 路由必须放在路由表最后。
- 页面跳转优先使用命名路由；禁止在业务代码中散落重复路径字符串。
- 二级页面必须提供返回控件，用户可见文案统一为“返回”，不得写成“返回列表”“返回上一级”等变体；跳转目标使用命名路由或可靠的历史返回逻辑。

示例：

~~~ts
{
  path: "/weekly-reports",
  name: "weekly-reports",
  component: () => import("@/views/weekly-report/IndexView.vue"),
  meta: { title: "周报管理" },
},
{
  path: "/weekly-reports/:id",
  name: "weekly-report-detail",
  component: () => import("@/views/weekly-report/DetailView.vue"),
  meta: { title: "周报详情" },
},
~~~

当 app/router/index.ts 超过 200 行时，必须拆分为 app/router/modules/<module>.ts，由 index.ts 汇总。

## 11. TypeScript 规范

- 必须保持 strict 模式通过。
- props、emits、接口响应、Store 状态必须有明确类型。
- 类型专用导入必须使用 import type。
- 禁止使用 any；外部不可信数据先使用 unknown，再完成类型收窄。
- 禁止无说明使用 @ts-ignore、@ts-nocheck 或双重类型断言。
- 领域类型放 features/<domain>/types.ts，通用类型放 shared/types/。
- 组件内部临时类型可就近声明，不为单次使用创建全局类型。

## 12. 样式规范

- 全局样式必须放在 src/styles/，并且只允许由 src/main.ts 导入 src/styles/index.css。
- tokens.css 只放主题变量和设计令牌；reset.css 只放浏览器重置；global.css 只放真正跨页面的基础元素或通用类。
- assets/ 只放图片、字体等静态资源，禁止再创建 assets/main.css。
- 页面或组件存在私有样式时，必须创建同目录、同名 CSS 文件，并使用 `<style scoped src="./文件名.css"></style>` 一对一引入。
- 没有私有样式的 Vue 文件不创建空 CSS 文件；一对一规则只约束确实存在的私有样式。
- 组件私有 CSS 必须使用 scoped；确需修改子组件内部结构时优先通过 props、slot 或 CSS 变量，最后才使用 :deep()。
- 多个组件共享的模块样式可放 views/<module>/styles/，不得提升到全局只为减少一次导入。
- 页面专属、模块专属或具体业务选择器禁止写入 global.css。
- 禁止使用无语义、依赖 DOM 顺序的选择器。
- 页面新增布局必须同时检查桌面端和窄屏状态。
- 新增颜色、间距等设计值优先复用现有 CSS 变量。

### 12.1 字体层级与颜色

默认字体只允许使用以下三档，除非产品需求或设计稿明确指定其他层级：

| 层级 | 字号 | 字重 | 颜色与用途 |
| --- | --- | --- | --- |
| 正文 | `14px` | `400`，不加粗 | 使用常规正文色；不使用标题级强色或纯黑强化效果 |
| 标题 | `16px` | `700`，加粗 | 使用标题主色（黑色或主题中最深的文字色）；不得再放大 |
| 缩小版文字 | `12px` | `400`，不加粗 | 使用辅助/弱化文字色；不使用标题级强色或纯黑强化效果 |

- 本规范中的“加黑”同时约束颜色和字重：标题使用标题主色与 `700` 字重；正文和缩小版文字不得通过纯黑颜色、`600+` 字重或额外字号来制造强调。
- 正文、标题和缩小版文字都不得使用 `clamp()`、断点放大或组件局部覆盖来无依据扩大字号；统一通过 `styles/tokens.css` 或设计系统令牌维护。
- Label、按钮、表头和表单内容默认按正文档处理；只有明确的页面层级才使用标题档或缩小档，不得为了突出视觉效果任意加粗或放大。

### 12.2 输入框 Placeholder

- `input`、`textarea` 等输入控件的 placeholder 默认沿用字段字号（通常为正文 `14px`），但必须使用 `font-style: italic`、较轻字重（优先 `300`，字体不支持时退回 `400`，不得加粗）和辅助文字色（如 `--text-placeholder`/`--muted`）。
- 正式输入内容必须保持正常字形、正文档字重（`font-style: normal`、`font-weight: 400`）和正文色；不得把 placeholder 的斜体、轻字重或弱化颜色应用到用户已经输入的值。
- Placeholder 与正式输入内容必须有清晰的视觉层级差异，但浅色不得接近不可见；优先使用专用颜色令牌，不要只依赖过低 `opacity` 制造区别。
- Placeholder 只提供简短输入示例或格式提示，不替代 Label，也不得塞入需求说明、实现规则、AI 提示词或长期操作提醒；必要字段名称仍须通过可见 Label 或无障碍名称提供。
- 使用组件库时优先通过组件的 placeholder/设计令牌配置；原生控件使用 `::placeholder` 或等价选择器，并检查聚焦、禁用、错误和窄屏状态。

标准示例：

~~~vue
<template>
  <section class="report-list">...</section>
</template>

<style scoped src="./ReportList.css"></style>
~~~

## 13. 界面文案、语言与布局密度

### 13.1 Label 与提示文案

- Label 只用于命名字段、操作或内容区域，应使用简短、明确的名词或动词短语。
- 禁止在 Label、标题、按钮、表头、占位符等位置附加与当前操作无直接关系的需求说明、业务规则解释、实现备注、AI 提示词、验收条件或开发过程信息。
- 用户给出的规则默认是实现约束，不是页面文案。应优先通过默认值、自动计算、可选范围、禁用状态和校验逻辑落实规则，不得把规则原样抄到页面上。
- 例如周期固定从周一开始、周日结束时，字段只显示“开始日期”和“结束日期”；通过日期选择范围与校验保证边界，禁止显示“开始日期（周一）”“结束日期（周日）”。
- 不展示“请按要求操作”“此处只能……”等长期占位的泛化操作提醒。只有信息直接影响用户当前的选择、输入、更正、状态判断或高风险操作时，才显示简短、可执行的提示，并在最相关的位置按需出现。
- 必要的字段校验、错误反馈、危险操作警告和确认信息不得省略；它们应描述问题及下一步，不得夹带开发规则或内部实现信息。
- 无障碍名称可以通过 `aria-label`、`aria-labelledby` 等非视觉方式提供，不得为了追求视觉简洁删除可访问性信息。
- 产品需求或设计稿明确指定的用户文案优先；若与本节冲突，应在交付说明中说明。

### 13.2 单语言呈现

- 同一界面在任一时刻只能呈现一种产品语言，禁止出现“姓名 / Name”“开始日期（Start Date）”等中英文并排 Label。
- 已接入 i18n 时，Label、按钮、标题、表头、提示、校验和空状态等所有用户可见文案必须使用翻译资源，并跟随当前语言切换；不得硬编码第二种语言作为补充解释。
- 未接入 i18n 的单语言项目只使用产品指定语言，不得自行添加对照翻译。
- 产品名、用户生成内容和行业通用缩写可以保留原文，但不得借此重复翻译同一个界面 Label。

### 13.3 紧凑布局

- 桌面端默认采用紧凑、信息密度适中的布局；优先使用项目设计系统或组件库已有的 `small`、`compact`、`dense` 等尺寸能力以及统一间距令牌。
- 相关字段、筛选条件和操作应就近分组。空间允许时，短字段和筛选项优先合理并排，避免每个控件独占整行或无条件拉伸至容器全宽。
- 按钮宽度应与内容和操作层级匹配；表格行、表单控件、标题、卡片内边距和区块间距不得在没有设计依据时使用大号规格。
- 避免为每个小区块套独立大卡片、重复标题或留出大面积装饰性空白；留白只用于表达层级、分组和可读性，不得把主要内容无意义地下推。
- 尺寸和间距应集中复用组件属性或 CSS 变量，禁止为实现紧凑效果在各页面散落互不一致的硬编码值。
- 紧凑不等于拥挤。文字必须可读，焦点状态必须清晰，键盘操作必须完整；窄屏或触控场景可改为纵向排列并保留合理点击区域。
- 页面完成前必须在常见桌面宽度和窄屏下检查首屏信息量、控件尺寸、分组、留白与溢出情况。

### 13.4 提醒与告警弹窗

- 提醒和告警类反馈必须统一通过同一个公共通知组件与通知 store 入口调用；当前项目对应 `components/feedback/NoticeCenter.vue` 与 `useNoticeStore`，提醒和告警只是其中的两种类型。只有需要用户确认或填写内容的阻塞式模态才使用 `components/overlay/BaseDialog.vue`；禁止在页面私有目录重新编写同类弹窗 DOM、CSS、状态或计时器。
- 非阻塞提醒默认显示 `2000ms` 后自动关闭；调用方不应在页面中重复实现 `setTimeout`。如有特殊时长，必须由公共组件或统一通知 store 提供受控配置。
- 告警默认不自动关闭，必须提供明确的手动关闭操作；关闭后不得由组件自行重新弹出，除非业务事件再次触发。
- 所有弹窗使用公共组件提供的固定宽度、固定高度预设。禁止使用 `width: auto`、`height: auto`、`max-content` 或依据消息长度动态改变外框尺寸；不同场景需要不同尺寸时，应选择另一个固定预设。
- 内容变长时，弹窗外框尺寸保持不变，内部通过换行、滚动容器或受控截断处理，不能通过放大弹窗来容纳内容；移动端可以切换到更小的固定预设，但仍不得随内容伸缩。
- 弹窗必须保留既有的可访问性语义、焦点管理、键盘关闭和清晰的关闭控件；固定尺寸不得以牺牲可读性或可操作性为代价。

## 14. 图表与图标规范

### 14.1 图表

- 数据图表必须使用主流、持续维护的图表控件或库，优先复用项目已经安装的方案，例如 ECharts、Chart.js 或 AntV。
- 禁止在业务代码中手写 SVG 的 path、rect、circle、text 等元素拼装静态图表，也禁止通过硬编码坐标模拟数据图表。
- 图表控件自身选择 SVG 或 Canvas 作为渲染器不属于手写 SVG，可以正常使用。
- 图表必须由真实数据和配置驱动，并处理容器尺寸变化；存在异步数据时，同时处理 loading、empty 和 error 状态。

### 14.2 文字与图标

- 在用户、产品需求或设计稿没有特别说明时，按钮、导航项、菜单项、标题、标签、链接、表头等文字前禁止添加 icon。
- 禁止为了“更丰富”或“更美观”自动在文字前添加装饰性图标。
- 明确要求使用图标时，优先复用项目现有图标库或设计系统；仅图标控件必须提供可访问名称，例如 `aria-label`。

## 15. 环境变量规范

- 浏览器可读取的环境变量必须以 VITE_ 开头。
- 新增变量必须同步更新 .env.example、相关环境文件和 src/env.d.ts。
- 禁止把密钥、密码、Token 或其他服务端秘密放入前端环境变量。
- 代码中必须提供合理默认值，或在缺少必要配置时给出明确错误。

## 16. 导入规范

- 跨层和跨目录导入使用 @/ 别名。
- 同一模块内部紧邻文件可使用 ./ 相对导入。
- 禁止使用 ../../../ 形式的深层相对路径。
- 导入顺序为：第三方依赖、项目绝对导入、当前模块相对导入。
- 禁止通过 index.ts 大量重新导出隐藏真实依赖；只在公共 API 边界使用 barrel 文件。

## 17. 新页面实施流程

新增页面必须按以下顺序执行：

1. 明确功能模块名和路由。
2. 创建 views/<module>/IndexView.vue。
3. 将独立 UI 区块创建到 views/<module>/components/。
4. 为有私有样式的 Vue 文件创建同名 scoped CSS 文件。
5. 有子路由时创建独立的 *View.vue。
6. 在 features/<domain>/types.ts 定义领域类型。
7. 在 features/<domain>/api.ts 接入接口。
8. 确认是否需要 feature store；不共享时不要创建 Pinia Store。
9. 在 app/router/ 注册懒加载路由和 meta.title。
10. 有数据图表时使用主流图表控件，并确认不是手写 SVG 静态图。
11. 检查 Label 和提示文案，只保留当前任务所需的信息，确认没有展示需求说明、实现约束或泛化操作提醒。
12. 检查同一界面只呈现一种语言；已接入 i18n 时验证文案随当前语言切换。
13. 检查桌面端布局密度、控件尺寸、分组和留白，并验证窄屏适配。
14. 检查正文、标题和缩小版文字是否分别符合 `14px/400`、`16px/700`、`12px/400`，并确认没有无依据的字号放大或颜色强化。
15. 检查输入框 placeholder 是否为斜体、较轻字重和辅助色，正式输入是否恢复正常字形与正文档字重。
16. 检查提醒/告警弹窗是否复用公共组件，确认提醒 `2000ms` 自动关闭、告警手动关闭且弹窗宽高来自固定预设。
17. 检查文字前是否存在未经明确要求的 icon。
18. 补充空状态、加载状态、错误状态和窄屏布局。
19. 执行完整检查。

## 18. 完成定义

新页面只有同时满足以下条件才算完成：

- [ ] views 根目录没有新增平铺的 *View.vue。
- [ ] 模块包含 IndexView.vue，子页面和组件已按职责拆分。
- [ ] IndexView.vue 没有直接发送 HTTP 请求。
- [ ] 页面私有组件未被其他 views 模块直接引用。
- [ ] API、Store、类型位于正确的 feature。
- [ ] 跨业务基础组件按功能分类位于 components/<category>/，components 根目录没有平铺组件。
- [ ] 纯工具函数和全局样式分别位于 utils、styles。
- [ ] 私有样式使用同目录同名 CSS，并通过 scoped style src 引入。
- [ ] global.css 中没有页面或业务专属选择器。
- [ ] Label 仅用于命名字段、操作或区域，没有附加需求说明、实现约束、AI 提示词或非必要操作提醒。
- [ ] 业务规则已通过交互和校验落实，没有被直接复制成常驻页面文案；必要的错误、风险警告和无障碍名称仍然完整。
- [ ] 同一界面只显示一种语言；i18n 文案跟随当前语言，单语言项目没有中英文对照 Label。
- [ ] 桌面端控件、字号、卡片、间距和留白保持紧凑且层级清楚，窄屏与键盘操作仍然可用。
- [ ] 默认正文为 `14px/400`，默认标题为 `16px/700`，缩小版文字为 `12px/400`；正文和缩小版文字没有无依据的加黑、加粗或放大。
- [ ] 输入框 placeholder 使用斜体、较轻字重和辅助色；正式输入内容使用正常字形、正文档字重和正文色。
- [ ] 提醒和告警类弹窗统一复用公共组件；提醒默认 `2000ms` 自动关闭，告警手动关闭。
- [ ] 弹窗宽高来自固定尺寸预设，内容变化不会导致外框自动缩放、放大或改尺寸。
- [ ] 数据图表使用主流图表控件，没有手写 SVG 静态图。
- [ ] 未经明确要求，文字前没有添加装饰性 icon。
- [ ] 没有硬编码 /api 域名、密钥或环境专属参数。
- [ ] loading、empty、error 和正常状态均有处理。
- [ ] TypeScript strict 校验通过。
- [ ] npm run type-check 通过。
- [ ] npm run build 通过。
- [ ] 文档与环境变量示例已同步更新。

## 19. 当前模块参考

- views/home/IndexView.vue：页面入口与生命周期。
- views/home/components/：首页私有区块。
- views/chat/IndexView.vue：聊天模块入口。
- views/chat/components/ChatPanel.vue：连接 Store 的容器组件。
- views/chat/components/ChatToolbar.vue：纯展示与事件组件。
- views/chat/components/ChatMessageList.vue：消息展示和滚动行为。
- views/chat/components/ChatComposer.vue：输入与提交组件。
- features/chat/：聊天领域的 API、Store 和类型。
- components/feedback/BaseAlert.vue：跨业务复用的全局基础提示组件。
- utils/id.ts：无业务语义的全局 ID 工具。
- styles/：全局样式入口、主题变量、重置和基础类。
- shared/api/：所有模块共用的 HTTP 与错误处理基础设施。

## 20. 前后端 API 对接契约

前端和后端只通过版本化 JSON API 协作。前端不关心 Django、Service、DAO、Model、SQL、Redis、AI SDK 等后端实现；后端不关心 Vue 页面、组件、CSS、Pinia 或布局。接口定义是唯一边界，页面设计不得改变接口语义。

每个 `features/<domain>/api.ts` 的请求函数必须写中文注释，至少说明：接口用途、HTTP 方法、完整路径（业务路径从 `/v1/` 开始，由统一客户端拼接 `/api`）、认证/权限/幂等要求；请求参数的位置、字段、类型、必填性、默认值、范围、枚举、单位、`null` 规则、示例和敏感字段加密要求；成功响应 JSON 的包络、字段含义/类型、空值/分页规则和示例；失败状态码、稳定错误码、展示策略、`trace_id`、脱敏和兼容性/版本策略。

前端 API 层必须定义请求、响应和错误 TypeScript 类型，并把后端响应映射为领域类型；页面和组件只调用领域 API/Store，不直接调用 Axios，不解析后端内部异常、ORM 字段、数据库结构或第三方响应。统一客户端负责 `/api` 前缀、`X-Trace-ID`、认证头和错误归一化，页面只处理 loading、empty、error 和展示。

统一数据约束：后端成功响应使用 `success: true`，失败响应使用 `success: false`、稳定 `error.code` 和 `trace_id`；64 位 Snowflake ID 在 JSON 中按字符串处理，日期时间使用带时区 ISO 8601，字段/枚举使用约定的 snake_case，金额/数量/时长标明单位，分页字段保持一致；密码必须先用 RSA-OAEP-SHA256 加密，前端不得记录或回传明文。

接口变更前先更新契约、中文注释和示例，再同步 API 类型、调用代码、契约测试和版本说明。新增字段默认兼容；删除、改名、改类型、改变语义或必填性必须升级主版本并保留迁移期。联调检查方法/路径、鉴权、请求、响应、错误、trace ID、ID/日期格式和版本兼容性全部一致。
