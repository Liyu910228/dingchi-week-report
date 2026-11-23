# 后端 Python 开发约束参考

本文是 `backend-python-development-conventions` skill 的详细参考。除非用户明确覆盖，以下“必须”和“禁止”均适用于新增、重构和审查的后端代码。

## 1. 技术边界与目录

默认技术栈：Python 3.12+、Django、ASGI、MCP、MySQL、Redis、OpenAI-compatible SDK。

```text
backend/
├─ config/                              # settings、根路由、ASGI/WSGI、生命周期装配
│  ├─ settings/{base,development,production,test}.py
│  ├─ urls.py
│  ├─ asgi.py
│  └─ wsgi.py
├─ apps/
│  ├─ core/                             # 横切基础设施，不承载业务领域
│  │  ├─ middleware/                    # trace、异常、安全响应头等
│  │  ├─ interceptors/                  # 接口级限流、幂等、审计、权限声明
│  │  ├─ authentication/                # 通用认证上下文
│  │  ├─ permissions/                   # 通用权限原语
│  │  ├─ security/                      # RSA、公钥接口、加密字段
│  │  ├─ models/base.py                 # 可复用抽象模型
│  │  ├─ services/                      # 平台服务和 ID 生成入口
│  │  └─ http.py                        # 统一 JSON 响应/错误
│  ├─ mcp_server/                       # 唯一 MCP Server 和工具注册边界
│  │  ├─ server.py
│  │  ├─ registry.py
│  │  └─ modules/<capability>/tools.py
│  └─ <domain>/                         # 业务模块
│     ├─ models/
│     ├─ views/
│     ├─ services/
│     ├─ dao/sql/                       # 多表关联 SQL
│     ├─ integrations/
│     ├─ policies/
│     ├─ urls.py
│     └─ tests/
├─ utils/                               # 无业务语义的纯工具
├─ scripts/                             # 显式运行的开发/部署/探测脚本
└─ docs/
```

只创建实际需要的可选目录。禁止把业务逻辑放入 `config/`、`utils/` 或 `scripts/`，禁止新增含义宽泛的 `common.py`、`helpers.py`、`misc.py`。

## 2. MVC、依赖方向和模块边界

### 2.1 MVC 映射

| 职责 | 位置 | 强制要求 |
| --- | --- | --- |
| Model | `apps/<domain>/models/` | 实体、字段、单实体不变量；不得访问协议或外部服务 |
| Controller/HTTP View | `apps/<domain>/views/` 或 `views.py` | 接收请求、认证授权入口、校验、调用 Service、返回 JSON |
| View representation | Django View + `apps/core/http.py` | 使用统一 `{"success": true/false, ...}` 包络 |
| Service | `services/` | 用例编排、事务、幂等、跨实体规则；不依赖 HTTP/MCP 对象 |
| DAO | `dao/` | ORM、参数化 SQL、持久化和数据库锁；不做业务决策 |
| Integration | `integrations/` | AI、第三方 HTTP、消息等 SDK 适配和错误映射 |

依赖方向固定为：

```text
urls → views → services → (policies / dao → models / integrations)
mcp_server/modules/* → public.py 或公开 Service
```

跨模块只依赖对方公开 `public.py`/Service；禁止导入对方 View、DAO、内部 Model 或 Integration。HTTP、MCP、脚本和任务必须复用同一个 Service，不复制业务规则。

### 2.2 View 和响应

- 每个 View 只做输入类型/边界校验、认证授权入口、拦截器调用、Service 调用和 JSON 映射。
- 禁止在 View 直接调用 ORM、Redis、AI/HTTP SDK、事务或复杂领域计算。
- 简单请求/响应类型就近定义；仅在跨入口且明显复杂时抽取语义明确的类型文件，不创建固定 `schemas/` 模板层。
- 所有 HTTP 响应必须由 `apps/core/http.py` 生成；错误码使用稳定的大写下划线格式，未知异常只返回安全通用文案。

## 3. 启动、路由、中间件和认证

### 3.1 启动与迁移

ASGI/WSGI、脚本、容器入口和健康检查只能加载配置、装配应用和启动服务。**禁止自动执行** `makemigrations`、`migrate`、建表、改表或密钥生成。迁移必须由开发者/部署流程显式审核和执行。

### 3.2 路由

- `config/urls.py` 只挂载模块路由；REST 统一 `/api/v1/`，路径使用小写名词和一致尾斜杠。
- MCP 只在 `config/asgi.py` 挂载 `/mcp/`，工具由 `apps/mcp_server/registry.py` 集中注册。
- 不为每个 MCP Tool 创建 REST 地址；MCP Tool 只做协议参数适配、认证上下文适配和公开 Service 调用。

### 3.3 中间件、拦截器、认证

- 全局中间件放 `apps/core/middleware/`，接口级前后置逻辑放 `apps/core/interceptors/`，顺序必须在配置中显式维护。
- 中间件保持轻量，不查业务模型、不调用 AI；未知异常记录后继续交由统一异常策略处理，不得吞异常。
- 所有新接口默认需要认证；认证只建立身份上下文，权限由通用原语和业务 Policy/Service 分工判断。
- 认证失败与权限不足分别返回 401/403；凭证、Cookie、Token、API Key 和完整 Authorization Header 不得写日志。

## 4. 数据库、DAO 和逻辑关联

- 单表过滤、排序、分页和简单写入使用 Django ORM，并集中在 DAO/Manager；View 和 Service 不直接写查询。
- 两个及以上表的关联查询必须放在 `dao/sql/<query>.sql`，由 DAO 以参数绑定执行；禁止 Python 字符串拼接 SQL，禁止用 ORM 关系拼接替代参数化 SQL。
- 表关联只使用标量 `*_id` 或显式中间表，禁止 `ForeignKey`、`OneToOneField`、默认 `ManyToManyField`、数据库外键约束和外键索引。完整性、删除策略和数据范围由 Service/DAO 校验。
- 所有写流程的 `transaction.atomic()` 在 Service；事务中不得执行耗时 AI/HTTP 调用。批量读写必须分页或分批并说明锁策略。
- MySQL 是业务事实来源；DAO 不访问 Redis、AI、HTTP 或 MCP。

## 5. 连接池和环境配置

- MySQL 连接必须使用适配器的持久连接/连接池能力；Redis 必须使用 `django-redis`/redis-py 连接池。禁止按请求临时创建连接。
- 池大小、最大连接数、获取/读写超时、健康检查、重试、连接复用和忽略异常策略全部来自 `.env.*`。
- 所有运行配置、域名、端口、连接字符串、密钥路径、AI 模型/超时和安全开关都必须通过 `.env.*` 注入；代码中不写秘密或环境专属值。
- 每个 `.env.*` 配置项必须有中文注释，说明用途、格式、单位和是否必填；同步维护 `.env.example` 与生产占位文件。
- 配置读取集中在 `config/settings/` 并完成类型转换；缺少必填项必须显式失败，不得用静默默认值掩盖。

## 6. 请求追踪和滚动日志

- 所有 HTTP、WebSocket 和 MCP 请求都经过 ASGI 外层与 Django middleware；合法的 `X-Trace-ID` 原样复用，缺失/非法则生成随机 trace ID。
- 响应必须带 `X-Trace-ID`；日志过滤器把当前 trace ID 注入每条应用日志。Django、ASGI、MCP 不得各自生成不同 ID。
- 日志使用 `logging.handlers.RotatingFileHandler`，UTF-8 编码；`LOG_LEVEL`、`LOG_DIR`、`LOG_FILE_NAME`、`LOG_MAX_BYTES`、`LOG_BACKUP_COUNT`、`LOG_CONSOLE_ENABLED` 等全部取自环境。
- 日志至少包含时间、级别、logger、trace ID、动作和结果；不记录密码明文、RSA 密文、私钥、公钥文件内容、Token、Cookie、完整 Authorization Header、完整 Prompt 或敏感业务原文。
- 路径/查询字符串也按敏感信息审查；异常堆栈只写服务端日志，不直接返回客户端。

## 7. 雪花主键

- `utils/snowflake.py` 实现线程安全、有序、64 位 Snowflake ID，处理序列耗尽等待下一毫秒，检测时钟回拨并显式失败。
- 新业务模型统一继承 `apps/core/models/base.py` 的 `SnowflakeIdModel`，或将 `id` 默认值指向 `apps/core/services/id_generator.py` 的 `generate_primary_id()`。
- `SNOWFLAKE_EPOCH_MS`、`SNOWFLAKE_WORKER_ID`、`SNOWFLAKE_DATACENTER_ID` 必须在 `.env.*` 配置；节点编号在实例间不可冲突。
- 禁止数据库自增、UUID、随机字符串或按业务自行生成主键；业务表主键字段/表名使用小写 snake_case。

## 8. RSA 密码传输与存储

- 统一算法是 `RSA-OAEP-SHA256`。前端通过 `/api/v1/security/public-key/` 获取 SubjectPublicKeyInfo PEM，再使用 Web Crypto 加密；页面/feature API 不得传密码明文或自行实现另一套算法。
- 后端统一从 `apps/core/security/` 加载密钥、解密客户端密文；明文只在请求内存短暂存在，不写日志、不放缓存、不返回响应。
- 数据库字段使用 `EncryptedPasswordField` 或 `encrypt_client_password_for_storage()`/`encrypt_password_for_storage()`，保存带 `rsa_oaep_sha256:` 版本前缀的密文。
- 私钥只通过 `CRYPTO_PRIVATE_KEY_PATH` 和 `CRYPTO_PRIVATE_KEY_PASSWORD` 注入服务端；前端 `VITE_*` 不得出现私钥、Token、密码或其他服务端秘密。密钥文件不得提交 Git。
- 密钥由 `scripts/generate_crypto_keys.py` 显式生成，禁止启动时自动生成/覆盖；轮换必须保留算法版本和迁移兼容策略。生产仍必须使用 HTTPS。

## 9. AI、Redis 和异步边界

- AI SDK 只放在 AI 模块的 `integrations/`/网关适配器，模型、Base URL、密钥和超时全部来自配置；业务层依赖本地接口/结果类型。
- AI 调用限制输入消息数、单条/总长度和输出上限；超时、限流、空结果、配置缺失和上游错误分别映射稳定错误。
- Redis 只能做缓存、锁、限流或临时状态，不能作为业务事实唯一来源；Key 必须集中构造并包含应用、环境、模块、用途、标识和版本，所有缓存项必须有 TTL/失效策略。
- 异步路径不能直接执行同步 ORM、文件 I/O 或阻塞 SDK；复用的 AI/HTTP 客户端在 ASGI lifespan 创建/关闭，不能每请求新建。

## 10. 命名、拆分和测试

- 表名、字段名、模块目录和 SQL 文件使用小写 snake_case；逻辑关联字段显式命名 `<entity>_id`。
- 系统/环境/全局变量按项目约定使用下划线开头的 snake_case；局部/临时变量以字母开头并使用 snake_case；错误码为大写下划线。
- 单函数超过 50 行、View 超过 80 行、文件超过 300 行且有多个职责，或同一逻辑出现第二次时必须按职责拆分。
- 测试覆盖 View 的认证/权限/响应、Service 的事务/幂等、DAO 的查询行为、Middleware 的顺序/上下文清理、Integration 的错误映射和 MCP 工具发现/参数校验。
- 测试不得依赖开发数据库、Redis、执行顺序或真实 AI/第三方服务；外部适配器使用 Mock/Fake。

标准验证：

```text
python -m ruff check .
python -m pytest
python manage.py check --settings=config.settings.test
python manage.py makemigrations --check --dry-run --settings=config.settings.test
```

交付前检查：无自动迁移/建表；无明文秘密和硬编码配置；MySQL/Redis 使用连接池；所有请求有 trace ID；新主键使用 Snowflake；密码使用 RSA 统一工具；REST/MCP 路由和模块依赖边界正确；文档、环境示例和测试已同步。

## 11. 前后端 API 对接契约

前端和后端只把版本化 JSON API 当作协作边界。前端不得依赖 Django View、Service、DAO、Model、SQL、Redis、AI SDK 或数据库实现；后端不得依赖 Vue 组件、路由页面、CSS、Pinia 状态或页面布局。双方只根据接口契约联调。

每个 REST、MCP 对外接口必须在后端 View/Tool 定义处写中文注释，至少说明：

- 接口用途、HTTP 方法、完整版本化路径（REST 为 `/api/v1/...`，MCP 统一从 `/mcp/` 进入）、认证方式、权限、幂等要求。
- 请求参数：参数位置（path/query/header/body）、字段名、类型、必填性、默认值、长度/范围、枚举、单位、是否允许 `null`、示例和敏感字段加密要求。
- 响应 JSON：成功包络、字段类型、字段含义、空值/空列表规则、分页结构、示例；不得直接序列化 ORM、异常对象或内部字段。
- 失败状态码和稳定错误码、客户端可展示文案、`trace_id` 返回位置、安全脱敏规则和向后兼容/版本策略。

后端实现顺序固定为 `View/Tool（认证、边界校验） → Service（用例） → DAO/Integration → 统一 JSON 响应`。View/Tool 负责契约映射，不把内部异常、SQL、第三方响应或页面需求泄漏给前端。成功响应使用统一 `success: true` 包络，失败响应使用 `success: false`、稳定 `error.code` 和 `trace_id`；同一路由不得混用多种格式。

前端 `features/<domain>/api.ts` 必须为每个请求函数写对应中文注释，并定义请求、响应和错误类型；页面只消费经过 API 边界映射后的类型，不解析 Axios 原始对象或后端内部包络。前后端共享以下数据约束：64 位 Snowflake ID 在 JSON 中始终为字符串；日期时间使用带时区的 ISO 8601；字段和枚举使用约定的 snake_case；金额、数量和时长明确单位；分页统一字段；密码只使用 RSA-OAEP-SHA256 加密传输，不在日志或响应中出现。

接口变更流程：先修改契约和中文注释，再同步后端校验/响应、前端 TypeScript 类型/调用、契约测试和变更记录；新增字段默认向后兼容，删除/改名/改类型/改变语义或必填性必须升级 `/v2/`（或项目约定的主版本）并保留迁移期。联调完成前检查方法、路径、鉴权、参数、响应、错误、trace ID、ID/日期格式和版本兼容性均有示例且测试通过。
