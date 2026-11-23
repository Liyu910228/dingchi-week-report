# 全局工具函数

此目录只存放无 Vue 状态、无 DOM 副作用、无具体业务归属的纯工具函数。

工具按职责拆分文件并使用具名导出。领域工具优先放到对应 features/<domain> 内，页面私有
逻辑放到 views/<module>/composables，禁止把所有函数堆入一个 utils.ts。

当前工具：

- `trace.ts`：生成请求追踪 ID，由 `shared/api/http.ts` 的请求拦截器统一使用。
