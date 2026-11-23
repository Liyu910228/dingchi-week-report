---
name: backend-python-development-conventions
description: "为 Python 3.12+、Django/ASGI/MCP 后端新增、重构或审查代码时，应用 MVC 分层、DAO/SQL、连接池、环境配置、请求追踪和密码安全规范；不用于前端或非 Python 服务。"
---

# Python 后端开发规范

用于在本地 Python 后端项目中新增功能、重构模块、修复缺陷或进行代码审查。目标是保持业务模块高内聚、跨层依赖单向、基础设施可配置，并让 HTTP、MCP、脚本复用同一业务用例。

## 开始前

1. 确认目标是 Python 3.12+、Django、ASGI、MCP、MySQL、Redis 或 OpenAI-compatible 后端；前端任务不使用本 skill。
2. 读取目标目录及父目录的 `AGENTS.md` 等项目指令，再完整阅读 [references/backend-development-conventions.md](references/backend-development-conventions.md)。
3. 检查现有 `config/`、`apps/`、`utils/`、`scripts/`、路由、配置文件、测试和运行入口；遵循已有边界，不为了“完整”创建空目录。
4. 明确用户授权范围。除非用户要求，不提交 Git、不修改外部系统、不执行数据库迁移或密钥轮换。

## 不可绕过的框架约束

- 业务位于 `apps/<domain>/`，模块内部按 Model、Django View（HTTP 控制层）、Service、DAO、Integration 分层；不要额外创建与 Django View 重复的 Controller 或固定 Schema 层。
- View 只做认证/权限入口、输入校验、Service 调用和统一 JSON 响应；禁止直接查询 ORM、Redis、AI SDK 或编写核心业务规则。
- 单表/简单查询使用 Django ORM；多表关联只能由 DAO 执行参数化 SQL 脚本。表关联使用逻辑 `*_id` 或中间表，禁止数据库外键、Django 外键关系和外键索引。
- 所有 MCP 工具只能放在 `apps/mcp_server/modules/<capability>/`，通过统一 `registry.py` 注册，统一挂载 `/mcp/`；REST 统一使用 `/api/v1/`。
- MySQL 和 Redis 必须使用连接池；池大小、超时、健康检查和重试参数全部由 `.env.*` 注入。所有运行配置、域名和秘密都必须在 `.env.*` 中有中文注释，禁止硬编码。
- 项目启动、健康检查和容器入口禁止自动执行 `makemigrations`、`migrate` 或任何建表/改表操作。
- 前后端只通过版本化 JSON API 契约协作；每个 REST 和 MCP 对外接口都必须有中文注释，说明接口用途、方法/路径、认证权限、请求参数与类型、响应 JSON、错误码、安全要求、`trace_id` 和兼容性；不得暴露后端内部实现，也不得把页面设计写入接口约束。

## 强制横切能力

- 所有 HTTP、WebSocket 和 MCP 请求经过 ASGI/Django trace middleware，生成或复用合法 `X-Trace-ID`；响应和日志复用同一值。
- 使用 `RotatingFileHandler` 记录 UTF-8 日志；级别、目录、文件名、单文件大小、保留数量和控制台开关从 `.env.*` 读取。禁止记录密码、RSA 密文、密钥、Token、Cookie 和完整 Authorization Header。
- 新业务主键使用 `utils/snowflake.py` 的雪花算法及 `apps/core/services/id_generator.py`（或统一抽象模型）；禁止自增、UUID 或随机字符串主键。节点编号和纪元时间来自环境配置。
- 页面密码使用 RSA-OAEP-SHA256 公钥加密后传输；后端只在内存中短暂解密，并使用统一加密字段/工具以 `rsa_oaep_sha256:` 前缀保存。私钥只从服务端环境配置的文件路径加载。

## 依赖与实现方式

保持 `urls → views → services → (dao/models、integrations、policies)` 的单向依赖；MCP Tool 只能依赖业务公开 Service/`public.py`。跨模块禁止导入对方 View、DAO 或内部 Model。

接口实现前先阅读项目级 `docs/frontend-backend-api-conventions.md`（若项目提供），先确定并记录 API 契约、中文接口注释和测试，再实现 View/Service/DAO。接口变更必须同步契约、前端类型和兼容性说明。

实现时优先复用项目已有适配器、统一响应、异常映射、认证、拦截器和连接池。新增配置要同步 `.env.example`、环境占位文件和文档；新增模型要显式设计逻辑关联、索引和迁移，但迁移只能由用户明确执行。

## 验证与交付

按项目实际工具运行并报告结果：

```text
python -m ruff check .
python -m pytest
python manage.py check --settings=config.settings.test
python manage.py makemigrations --check --dry-run --settings=config.settings.test
```

涉及前端联调时额外验证 `npm run type-check` 和 `npm run build`；涉及密钥时只验证公钥接口和加解密行为，不输出密钥内容。交付说明应列出变更文件、验证命令、未执行的迁移/部署步骤及任何规范偏离。
