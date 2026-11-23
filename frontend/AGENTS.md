# Frontend workspace instructions

在 frontend 目录内新增或修改页面前，必须完整阅读并遵守：

- docs/frontend-development-conventions.md

不可绕过的核心规则：

1. 禁止在 src/views 根目录新增平铺的 *View.vue。
2. 每个功能模块使用 src/views/<module>/IndexView.vue 作为主入口。
3. IndexView.vue 只做页面编排、页面级生命周期和少量事件协调。
4. 页面私有组件放入本模块 components/，独立子页面创建独立 *View.vue。
5. 跨页面领域逻辑放 features；跨业务基础组件按功能分类放入 components/<category>/，禁止平铺在 components 根目录；纯工具函数放 utils；HTTP 等共享基础设施放 shared。
6. 全局样式统一放 styles；组件或页面的私有样式使用同名 .css 文件，并通过 scoped style src 引入。
7. 图表使用主流图表控件，禁止手写 SVG 静态图；没有特别说明时，文字前禁止添加装饰性 icon。
8. 页面和组件禁止直接调用 Axios；统一通过 shared/api/http.ts 和 feature api.ts。
9. 必须遵守规范中的文件拆分阈值和单向依赖规则。
10. 完成修改后必须运行 npm run type-check 和 npm run build。
11. 所有请求必须经 `shared/api/http.ts`，由请求拦截器统一附加 `X-Trace-ID`；页面不得直接使用 Axios。
12. 页面密码必须调用 `shared/security/password.ts` 通过 RSA-OAEP-SHA256 公钥加密后提交，禁止明文、私钥或密钥配置进入前端环境变量、日志和 Store。
13. 加密失败必须阻止请求并展示错误状态，不得降级发送明文密码。
14. 前后端只依赖版本化 API 契约；每个 feature API 接口必须有中文注释，说明用途、请求参数、响应数据、错误码、安全、trace_id 和兼容性。
15. 页面只依赖 TypeScript API 类型和 JSON 数据，不读取后端内部实现；64 位 ID 按契约使用 string，接口变更必须同步类型、注释、Mock/测试并遵守版本兼容规则。
16. 前端页面标题下禁止添加副标题或页面用途说明；列表布局优先参考现有周报列表。必要的业务告警、校验信息仍按实际状态显示。

17. 用户可见的身份称谓统一使用“职位”；代码中的 role、role_code 和既有接口标识保持不变。

如果用户的明确要求与规范冲突，以用户要求为准，并在交付说明中指出偏离项。
