# Backend workspace instructions

在 `backend` 目录内新增或重构后端代码前，必须完整阅读并遵守：

- `docs/backend-development-conventions.md`

不可绕过的核心规则：

1. 业务代码必须按 `apps/<domain>/` 聚合，并在模块内部按 MVC 职责分层。
2. Django View 统一承担 HTTP 控制层职责，不再单独建立 Controller 或固定 Schema 层；Service、DAO 和 Integration 必须保持规范定义的单向依赖。
3. Django View 只处理认证授权入口、参数校验、Service 调用和统一 JSON 响应，禁止直接写 ORM 查询或核心业务规则。
4. 跨业务模块调用只能依赖对方公开接口，禁止导入其他模块的 View、DAO 或内部 Model 实现。
5. 全局中间件、拦截器、认证和通用权限能力统一放在 `apps/core/` 对应子目录，业务权限规则留在所属业务模块。
6. REST 路由统一使用 `/api` 前缀，MCP 路由统一使用 `/mcp` 前缀；根路由只做模块挂载。
7. 所有 MCP 工具必须统一放在 `apps/mcp_server/modules/<capability>/`，按功能模块分层管理；
   业务模块不得新增 `mcp/` 工具目录，工具通过 `registry.py` 由统一 Server 注册。
8. 项目启动及健康检查禁止自动执行 `makemigrations`、`migrate` 或任何建表/改表操作；迁移必须显式执行。
9. 单表/简单查询必须使用 Django ORM；多表关联查询必须由 DAO 执行参数化 SQL 脚本，禁止在 View/Service 直接写查询。
10. 表关联只允许逻辑关联，禁止数据库外键约束、Django 外键关系字段和外键索引；使用 `*_id` 等标量字段或显式中间表。
11. 表名、字段名统一使用小写 snake_case；系统/环境/全局变量以下划线开头并使用 snake_case；局部/临时变量以字母开头并使用 snake_case。
12. 数据库连接和 Redis 连接必须使用连接池；连接池参数必须由 `.env.*` 注入，禁止按请求临时创建连接。
13. 所有系统配置变量必须放在 `.env.*` 文件，并为每项配置添加中文用途、单位、必填性和格式注释；禁止在代码中硬编码。
14. 无业务语义的纯工具放 `utils/`，运维开发脚本放 `scripts/`，环境与应用装配置于 `config/`，禁止把业务逻辑放入这些目录。
15. 数据库事务放在 Service 层；Redis 只作为缓存、锁或临时状态，不作为业务事实唯一来源。
16. 密钥和环境差异只能通过环境配置注入，禁止硬编码或写入日志。
17. 完成修改后必须运行 Ruff、Pytest 和 Django system check；涉及模型时还要检查迁移文件。
18. 所有 HTTP、WebSocket 和 MCP 请求必须经过统一 trace middleware；请求、响应和日志复用同一 `X-Trace-ID`。日志滚动方式、目录、级别和保留数量必须全部由 `.env.*` 配置。
19. 新业务表主键必须通过 `apps/core/services/id_generator.py` 使用 `utils/snowflake.py` 雪花算法生成，禁止自增、UUID 或随机字符串主键。
20. 页面密码必须使用 RSA-OAEP-SHA256 公钥加密传输，后端统一解密并使用加密字段保存；私钥仅服务端配置注入，禁止把明文、密文或密钥写入日志。
21. 前后端只依赖版本化 API 契约；每个接口必须有中文注释，说明用途、请求参数、响应数据、错误码、安全、trace_id 和兼容性，禁止暴露后端内部实现或页面设计。
22. 接口成功/失败必须返回统一 JSON 包络；64 位 Snowflake ID 以字符串传输，时间/分页/单位/空值语义必须在契约中明确，破坏性变更必须升级 API 版本。

如果用户的明确要求与规范冲突，以用户要求为准，并在交付说明中指出偏离项。
