---
name: frontend-backend-api-conventions
description: "定义前后端按版本化 JSON API 契约协作的规则；适用于接口设计、实现、联调、审查和变更，不用于页面视觉设计或后端内部重构。"
---

# 前后端 API 对接规范

使用本 skill 时，先读取目标目录及父目录的 `AGENTS.md`，再完整阅读 [references/frontend-backend-api-conventions.md](references/frontend-backend-api-conventions.md)。若项目提供仓库级 `docs/frontend-backend-api-conventions.md`，也要以其最新约束为准。除非用户明确覆盖，本文中的“必须”和“禁止”均为强制规则。

## 核心边界

- API 契约是前后端唯一协作边界。前端只依赖方法、路径、请求/响应 JSON、错误码和版本；不得依赖 Django、Service、DAO、Model、SQL、Redis、AI SDK 等后端实现。
- 后端只实现稳定的数据契约和业务语义；不得依赖 Vue 页面、组件、CSS、Pinia、路由布局或视觉设计。页面需求通过数据字段和接口语义表达，不把页面结构塞进 API。
- 同一接口只能有一份方法、路径和版本定义。REST 统一从 `/api/v1/` 进入；MCP 统一从 `/mcp/` 进入并按工具契约描述参数。

## 每个接口必须有中文契约注释

在后端 Django View/MCP Tool 定义处，以及前端 `features/<domain>/api.ts` 请求函数处，都必须写中文注释。注释至少包含：

1. 用途：接口解决什么业务问题、返回什么结果。
2. 方法与路径：HTTP 方法、完整版本化路径、认证权限、幂等要求。
3. 请求：path/query/header/body 参数位置、字段名、类型、必填性、默认值、长度/范围、枚举、单位、`null` 规则、示例；密码等敏感字段注明 RSA 加密要求。
4. 响应：成功 JSON 包络、字段类型和含义、空值/空列表、分页规则、完整示例；说明前端实际可消费的数据。
5. 失败：HTTP 状态码、稳定错误码、客户端处理/展示策略；不得把堆栈、SQL、ORM 或第三方原始错误返回给前端。
6. 横切要求：`trace_id` 的请求头和响应位置、脱敏要求、兼容性、版本升级和迁移期说明。

推荐注释结构：

```text
接口用途：查询当前用户的周报列表。
方法/路径：GET /api/v1/weekly-reports/
认证/权限：Bearer Token；仅允许查询当前用户可见数据；幂等：是。
请求参数：page（query，integer，默认 1，>=1）；page_size（query，integer，默认 20，1-100）。
成功响应：200，JSON 为统一 success 包络，items[].id 为字符串，时间为带时区 ISO 8601；分页字段见契约。
失败响应：401 AUTH_REQUIRED；403 FORBIDDEN；422 INVALID_PARAMETER；均返回 error.code、message、trace_id。
追踪/兼容：请求可带 X-Trace-ID，响应必带同值；新增字段向后兼容，破坏性修改升级主版本。
```

## 数据和安全规则

- 成功响应统一使用 `{"success": true, "data": ...}`；失败响应统一使用 `{"success": false, "error": {"code": "...", "message": "...", "details": ...}}`，并在响应头返回 `X-Trace-ID`（JSON 可按项目契约同时带 `trace_id`）。字段命名、包络和错误码不可在同一路由混用。
- 只返回前端完成任务所需的稳定白名单字段；禁止直接序列化 ORM、Model、异常、SQL、Redis 或第三方响应对象。
- 64 位 Snowflake ID 在 JSON 中始终使用字符串，前端 TypeScript 也声明为 `string`；日期时间使用带时区的 ISO 8601；金额、数量、时长必须写明单位；分页、`null` 和空列表遵循项目契约。
- 所有请求带 `X-Trace-ID`（缺失/非法则由后端生成），响应头和日志复用同一值。不得在日志、错误详情或响应中泄露密码、RSA 密文、密钥、Token、Cookie、完整 Authorization Header 或敏感业务原文。
- 页面密码使用约定的 RSA-OAEP-SHA256 公钥加密后传输；不在 API、Store、日志或 URL 中出现明文密码。

## 双方实施边界

### 后端

按 `View/Tool（认证、参数校验、契约映射） → Service（用例） → DAO/Integration → 统一 JSON 响应` 实现。View/Tool 不直接承载核心业务、ORM、Redis、AI/HTTP SDK 或 SQL；内部异常映射为稳定错误码并记录服务端日志。先写/更新中文契约注释、类型、示例和契约测试，再写实现。

### 前端

每个领域接口放在 `features/<domain>/api.ts`，请求/响应/错误都有明确 TypeScript 类型；统一 HTTP 客户端负责 `/api` 前缀、认证头、`X-Trace-ID` 和错误归一化。页面和组件只调用领域 API/Store，不能直接 import Axios 或解析后端内部包络；页面只处理 loading、empty、error 和展示映射。

## 变更与联调流程

1. 明确业务语义、方法、版本、鉴权、幂等和字段单位。
2. 先更新 API 契约、中文注释、请求/响应示例和错误码。
3. 同步后端校验/响应、前端类型/API 函数、契约测试和变更记录。
4. 联调只按契约验证，不要求前端理解后端实现，也不让后端适配页面 DOM/CSS。
5. 新增字段默认向后兼容；删除、改名、改类型、改变语义或必填性必须升级主版本（如 `/v2/`）并保留迁移期。
6. 完成前检查方法/路径、认证、请求、响应、错误、`trace_id`、ID/日期格式、脱敏和版本兼容性均一致。

## 验证要求

- 后端至少运行项目规定的静态检查、测试和 Django check；检查接口注释、统一 JSON、错误码、认证、trace ID 和响应字段。
- 前端至少运行类型检查和生产构建；检查 API 函数注释、请求/响应类型、错误处理、`/api` 前缀和 ID 字符串化。
- 契约发生变化时，必须报告修改的契约、兼容性策略、测试命令和未执行的迁移/部署步骤。不要提交 Git，除非用户另有要求。
