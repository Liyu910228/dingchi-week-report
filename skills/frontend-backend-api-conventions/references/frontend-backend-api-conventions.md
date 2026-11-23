# 前后端 API 对接约束参考

本文是 `frontend-backend-api-conventions` skill 的详细参考。适用于 Vue 3/Vite 前端与 Python/Django/MCP 后端，也适用于同一仓库中的其他前后端组合。除非用户明确覆盖，以下“必须”和“禁止”均适用于接口设计、实现、联调、审查和变更。

## 1. API 是唯一协作边界

前后端通过稳定、版本化的 API 契约协作。前端只需要知道接口方法、路径、认证方式、请求参数、响应 JSON、错误码和兼容性；不得依赖 Django View、Service、DAO、Model、SQL、Redis、AI SDK、数据库字段或后端目录结构。后端只需要实现契约定义的业务语义和数据；不得依赖 Vue 页面、组件、CSS、Pinia、路由布局或设计稿的 DOM 结构。

页面设计、数据库结构和内部实现都不是 API 契约的一部分。页面需要什么数据，应该通过稳定字段、枚举、分页和错误语义表达；实现替换只要契约不变，另一端不应修改代码。

## 2. 契约来源、版本和路径

- 每个接口只能有一个权威定义，至少包括方法、路径、版本、用途、认证、请求、响应、错误和兼容性。
- REST 统一使用 `/api/v1/` 前缀，资源路径使用小写 snake_case 名词和一致的尾斜杠；破坏性变更使用 `/api/v2/` 或项目明确约定的主版本。
- 前端 `VITE_API_BASE_URL` 只承载 `/api` 前缀，业务 API 函数填写 `/v1/...`，禁止硬编码域名、端口或完整 URL。
- MCP 统一从 `/mcp/` 进入，工具放在后端 `apps/mcp_server/modules/<capability>/`，工具名、参数和结果也必须按本文写中文契约注释。MCP 工具不另造重复 REST 地址。
- 接口变更先更新契约和注释，再同步两端实现、类型、测试和变更记录；新增字段默认向后兼容，删除、改名、改类型、改变语义或必填性属于破坏性变更，必须升级主版本并保留迁移期。

## 3. 每接口中文注释（强制）

后端 Django View、MCP Tool 和前端 `features/<domain>/api.ts` 的每个对外请求函数都必须有中文注释。注释不能只写“获取列表”这类标题，必须让未阅读实现的人仅凭注释完成调用。

注释至少包含以下内容：

| 项目 | 必须说明 |
| --- | --- |
| 用途 | 接口做什么业务动作，返回什么结果，数据范围是什么 |
| 方法/路径 | HTTP 方法、完整版本化路径；MCP 工具名和入口 |
| 认证/权限 | 是否需要登录、凭证位置、权限条件、数据隔离规则 |
| 幂等 | 是否幂等；重试、幂等键及重复提交行为 |
| 请求参数 | path/query/header/body 位置、字段名、类型、必填性、默认值、长度/范围、枚举、单位、`null` 规则、示例 |
| 敏感字段 | 密码、Token、个人信息等传输/脱敏/加密要求 |
| 成功响应 | HTTP 状态、JSON 包络、字段含义和类型、空值/空列表、分页、示例 |
| 失败响应 | HTTP 状态码、稳定错误码、客户端处理方式、字段校验详情 |
| 追踪与日志 | `X-Trace-ID` 输入/输出位置、脱敏和日志限制 |
| 兼容性 | 当前版本、字段演进、迁移期和升级方式 |

推荐后端 Python 注释：

```python
def list_reports(request: HttpRequest) -> JsonResponse:
    """查询当前用户可见的周报列表。

    方法/路径：GET /api/v1/weekly-reports/
    认证/权限：Bearer Token；仅允许当前用户可见数据；幂等：是。
    请求参数：page（query，int，默认 1，>=1）；page_size（query，int，默认 20，1-100）。
    成功响应：200，统一 success 包络；items[].id 为字符串，时间为带时区 ISO 8601。
    失败响应：401 AUTH_REQUIRED；403 FORBIDDEN；422 INVALID_PARAMETER；均返回 trace_id。
    兼容性：新增字段向后兼容，删除或改类型需升级主版本。
    """
```

推荐前端 TypeScript 注释：

```ts
/**
 * 查询当前用户可见的周报列表。
 * 方法/路径：GET /api/v1/weekly-reports/；认证：Bearer Token；幂等：是。
 * 请求：page/pageSize 转为 query 的 page/page_size，均为可选整数，范围见契约。
 * 响应：返回 WeeklyReportPage；id 按 string 处理，时间为带时区 ISO 8601。
 * 失败：AUTH_REQUIRED、FORBIDDEN、INVALID_PARAMETER 由统一错误层归一化；响应带 trace_id。
 */
export function getWeeklyReports(params: WeeklyReportQuery): Promise<WeeklyReportPage> {
  // ...
}
```

## 4. 请求规范

### 4.1 方法语义

| 方法 | 用途 | 约束 |
| --- | --- | --- |
| GET | 查询 | 参数放 query/path；不得产生业务副作用 |
| POST | 创建或触发非幂等动作 | 重试可能重复时必须设计幂等键 |
| PUT | 完整替换 | 说明缺失字段的替换语义 |
| PATCH | 部分更新 | 明确未传、传 `null` 和空值的区别 |
| DELETE | 删除/停用 | 说明软删、重复调用和数据可见性 |

请求参数必须注明位置。path 只放资源标识；query 用于过滤、排序、分页；header 用于认证、追踪和幂等键；body 使用 JSON。不得把密码、Token 或可变大段数据放 URL。未知字段、超长字符串、越界数值和不支持枚举必须在边界拒绝并返回稳定校验错误。

### 4.2 命名和数据类型

- JSON 字段和枚举使用项目约定的 snake_case；前端可以在 API 边界映射为 camelCase，但不能把映射规则隐含在页面中。
- 64 位 Snowflake ID 在 JSON 中始终是字符串，禁止让 JavaScript Number 承载；前端 TypeScript 类型必须写 `string`。
- 日期时间使用带时区的 ISO 8601，例如 `2026-09-09T10:20:30+08:00`；日期、时间和时区含义在注释中区分。
- 金额、数量、百分比、时长必须注明单位、精度和舍入规则；不要用含义不明的 `value`、`data` 或 `flag`。
- 明确字段是否可为 `null`、空字符串、空数组或缺省；同一字段不得在不同接口随意改变语义。

## 5. 统一 JSON 响应

推荐成功格式：

```json
{
  "success": true,
  "data": {
    "items": [
      {"id": "1888888888888888888", "title": "本周周报"}
    ],
    "page": 1,
    "page_size": 20,
    "total": 1
  },
  "trace_id": "01J..."
}
```

推荐失败格式：

```json
{
  "success": false,
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "请求参数不合法",
    "details": {"page_size": "必须在 1 到 100 之间"}
  },
  "trace_id": "01J..."
}
```

规则：

- 同一路由必须始终使用统一包络；不能一次返回裸数组、一次返回包络。
- 只返回前端完成任务所需的稳定白名单字段。禁止直接序列化 ORM、Django Model、异常对象、SQL 结果、Redis 值、AI/第三方原始响应。
- 列表、分页、详情、创建和更新的响应结构都要在注释中给出；空列表返回 `[]`，不要用 `null` 代替集合，除非契约明确规定。
- HTTP 状态表达大类，`error.code` 是可稳定判断的机器码；错误 `message` 是安全、可本地化的提示，不承诺内部异常文本。
- `trace_id` 可以置于响应字段，但必须置于 `X-Trace-ID` 响应头（项目统一实现以响应头为准）；注释中写清位置，前端错误上报必须保留它。

## 6. 状态码和错误码

至少统一以下映射：

| HTTP | 错误码示例 | 含义和前端动作 |
| --- | --- | --- |
| 400 | `MALFORMED_REQUEST` | JSON/协议错误，提示并停止重试 |
| 401 | `AUTH_REQUIRED`、`AUTH_INVALID` | 清理失效会话并转登录 |
| 403 | `FORBIDDEN` | 无权限，展示无权状态 |
| 404 | `RESOURCE_NOT_FOUND` | 展示不存在/已删除状态 |
| 409 | `CONFLICT`、`IDEMPOTENCY_CONFLICT` | 提示冲突，按契约决定是否重试 |
| 422 | `INVALID_PARAMETER` | 展示字段校验，不盲目重试 |
| 429 | `RATE_LIMITED` | 按 `Retry-After` 或退避策略重试 |
| 500 | `INTERNAL_ERROR` | 展示通用错误并携带 trace_id |
| 502/503/504 | `UPSTREAM_ERROR`、`SERVICE_UNAVAILABLE`、`UPSTREAM_TIMEOUT` | 安全提示并按契约有限重试 |

错误码一经对外使用不得静默改含义。新增错误码要补充注释、类型（如前端有枚举）和契约测试。

## 7. 安全、认证和追踪

- 所有新接口默认需要认证；注释写明 Bearer、Cookie、API Key 或其他凭证位置，以及权限和数据隔离条件。认证失败返回 401，认证成功但无权返回 403。
- 页面密码统一用 RSA-OAEP-SHA256 公钥加密传输；后端只在内存短暂解密并用统一加密字段/工具保存，明文和密文都不得进入日志、URL、缓存或普通响应。
- 前端每次请求添加或复用合法 `X-Trace-ID`；后端全局中间件生成/复用并在响应头和 JSON 错误中返回，HTTP、WebSocket、MCP 和日志使用同一个值。
- 日志和错误详情不得出现密码、RSA 密文、私钥、公钥文件内容、Token、Cookie、完整 Authorization Header、完整 Prompt 或敏感业务原文。前端只把安全错误信息展示给用户。

## 8. 前端实现边界

- API 函数位于 `features/<domain>/api.ts`，请求、响应、错误和分页类型位于领域 `types.ts` 或就近类型文件。
- 所有请求通过 `shared/api/http.ts`；页面/组件禁止 import Axios、拼接完整后端 URL 或读取原始 Axios 响应。
- 统一客户端负责 `/api` 前缀、认证头、`X-Trace-ID`、超时和错误归一化；领域 API 负责参数映射和后端字段到页面领域模型的白名单映射。
- 页面只调用领域 API/Store，并处理 loading、empty、error、成功展示和用户交互；不把接口字段解析、错误码分支和数据转换散落到多个组件。

## 9. 后端实现边界

- 后端按 `View/Tool → Service → DAO/Integration → 统一 JSON` 分层。View/Tool 负责认证入口、边界校验、契约映射；Service 负责用例、事务和幂等；DAO/Integration 负责持久化/外部适配。
- View/Tool 禁止直接写 ORM、SQL、Redis、AI/HTTP SDK 或复杂业务规则；Service/DAO 不返回页面组件需要的临时结构，而返回稳定领域结果，由边界层映射白名单 JSON。
- 内部异常、数据库错误、第三方原始响应、堆栈和敏感字段只写脱敏服务端日志，客户端只得到稳定状态码、错误码、提示和 trace_id。
- REST 和 MCP 可以共享同一个 Service，但不能复制业务规则或让 MCP/页面依赖另一入口的内部对象。

## 10. 契约测试和交付清单

契约测试至少覆盖：方法和路径、认证/权限、必填/类型/范围/枚举校验、成功 JSON 字段和类型、空列表/分页、每类错误码、trace_id、敏感字段脱敏、ID/日期格式和版本兼容。

联调交付前逐项确认：

- [ ] 每个 REST/MCP 接口和前端 API 函数都有完整中文注释、请求/响应示例。
- [ ] 方法、路径、版本、认证、权限、幂等要求一致。
- [ ] 请求位置/类型/必填/范围/单位/`null` 规则一致。
- [ ] 成功/失败 JSON 包络、字段白名单、分页和空值规则一致。
- [ ] HTTP 状态码、稳定错误码、展示/重试策略和 trace_id 一致。
- [ ] Snowflake ID 为 JSON 字符串，日期时间带时区，敏感字段遵守 RSA/脱敏规则。
- [ ] 前端无 Axios 越层、完整 URL 或后端内部字段依赖；后端无页面/CSS/组件依赖。
- [ ] 破坏性变更已升级主版本并保留迁移期，类型、测试、文档和变更记录已同步。
