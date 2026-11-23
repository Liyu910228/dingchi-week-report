# Backend

Django 6 + MCP 2 的 ASGI 后端，使用 MySQL 持久化、Redis 缓存，并通过 OpenAI-compatible SDK 调用大模型。

新增或重构后端代码必须遵守 [后端开发约束规范](docs/backend-development-conventions.md)，前后端接口还必须遵守仓库级 [API 对接规范](../docs/frontend-backend-api-conventions.md)。业务模块统一放在 `apps/<domain>/`，模块内部按 MVC、Service、DAO 和 Integration 分层；Django `views` 统一承担 HTTP 控制层职责，并通过 `apps/core/http.py` 返回统一 JSON 响应。

## 结构

```text
config/
├─ settings/            # base、development、production、test
├─ asgi.py              # Django 与 MCP 的统一 ASGI 入口
└─ urls.py              # /api 路由入口
apps/
├─ core/                # 通用响应、追踪中间件、认证和安全工具
├─ accounts/            # 登录、角色、用户、上下级和分组
├─ dictionary/          # 静态字典（角色数据范围、周报模板等）
├─ weekly_report/       # 模板、周报任务、指标、佐证和通用附件关联
├─ ai_gateway/          # AI 参数校验、服务层、HTTP 接口
└─ mcp_server/          # 统一 MCP Server，工具按 modules/<capability>/ 分层
```

横切能力说明：

- 所有 REST、MCP 和 WebSocket 请求统一生成/复用 `X-Trace-ID`，响应和滚动日志都会带上该值。
- 雪花主键通过 `apps/core/services/id_generator.py` 统一生成，配置项位于 `.env.*`。
- 页面密码使用 RSA-OAEP-SHA256 公钥加密；公钥接口为 `GET /api/v1/security/public-key/`，后端密码字段以 `rsa_oaep_sha256:` 前缀保存。
- 项目启动不会自动生成密钥或执行数据库迁移。首次开发需显式运行：

```powershell
python scripts/generate_crypto_keys.py
```

## 启动

在 Windows **CMD（命令提示符）** 中执行：

```bat
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -e ".[dev]"
python -m uvicorn config.asgi:application --reload --port 8000
```

在 Windows **PowerShell** 中执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m uvicorn config.asgi:application --reload --port 8000
```

说明：`Activate.ps1` 是 PowerShell 脚本，不能在 CMD 中使用；CMD 必须使用
`.venv\Scripts\activate.bat`。如果 PowerShell 提示禁止执行脚本，可仅对当前用户执行一次：

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

不要用 `manage.py runserver` 作为完整项目入口，因为它不会承载顶层 Starlette 中的 MCP 生命周期。

项目启动不会自动执行数据库迁移。数据库变更必须单独审核并手动执行：

```powershell
python manage.py makemigrations
python manage.py migrate --plan
python manage.py migrate
```

纯 SQL 初始化脚本统一放在 `docs/数据库脚本/`：

```powershell
mysql -uroot -p dingchi_week_report < "docs/数据库脚本/01_建表DDL.sql"
mysql -uroot -p dingchi_week_report < "docs/数据库脚本/02_初始化DML.sql"
```

其中 DDL 使用 `CREATE TABLE IF NOT EXISTS`，不会覆盖已有表；日期时间字段统一为
`DATETIME(6)`。`99_删除所有表.sql` 为破坏性脚本，仅限确认目标数据库后执行。手工 DDL
与 Django migration 二选一作为同一环境的结构初始化来源，禁止在启动命令中自动执行。

## API 响应约定

成功：

```json
{"success": true, "data": {}}
```

失败：

```json
{"success": false, "error": {"code": "ERROR_CODE", "message": "错误说明"}}
```

## 周报与组织接口

- `POST /api/v1/auth/login/`、`GET /api/v1/auth/me/`、`POST /api/v1/auth/switch-role/`：登录、会话和角色切换。
- `GET /api/v1/dashboard/summary/`：按当前角色返回个人、团队或全量驾驶舱数据。
- `GET /api/v1/weekly-report-templates/{template_code}/`：按包含版本号的模板编码获取模板任务、指标和列表字段。
- `GET/POST /api/v1/weekly-reports/`、`GET/PATCH/DELETE /api/v1/weekly-reports/{id}/`：查询、创建、编辑和删除周报。
- `GET/POST /api/v1/weekly-reports/{id}/daily-tasks/`、`PATCH/DELETE /api/v1/weekly-reports/{id}/daily-tasks/{daily_task_id}/`：查询、新增、编辑和删除周报每日工作任务；日报表需先执行 `backend/docs/数据库脚本/06_新增每日工作任务表.sql`。
- `POST /api/v1/weekly-reports/{id}/attachments/`：上传周报附件，附件记录写入通用 `system_attachment` 表。
- `GET /api/v1/users/`、`GET /api/v1/roles/`、`GET /api/v1/groups/`：总裁/系统管理员维护组织主数据。

角色范围和周报模板均从 `system_dictionary` 字典表读取，初始范围编码为 `self`（本人）、`team`（本人及下属树）和 `all`（全量）。所有接口返回统一 JSON，并附带 `X-Trace-ID`；完整中文契约注释放在后端 `views.py` 与前端 feature `api.ts`。

## 环境配置

环境变量按应用运行、跨域安全、静态/附件、MySQL、Redis、AI、雪花主键、认证、RSA
和日志等模块分组维护；每个配置项都在 `.env.*` 文件中保留中文说明。配置文件的职责如下：

- `.env.example`：不含真实凭据的公共占位示例。
- `.env.development`：本地开发配置，使用本机 MySQL/Redis；开发机可直接修改其中的连接参数。
- `.env.production.example`：生产配置模板，不可直接用于生产；复制为未提交的 `.env.production` 后，再替换全部 `CHANGE_ME` 占位符。

生产环境示例（Linux/macOS）：

```bash
cp .env.production.example .env.production
export ENV_FILE=/opt/dingchi-week-report/backend/.env.production
export DJANGO_SETTINGS_MODULE=config.settings.production
python -m uvicorn config.asgi:application --host 0.0.0.0 --port 8000
```

Windows PowerShell 可使用 `$env:ENV_FILE` 和 `$env:DJANGO_SETTINGS_MODULE` 设置同名变量后启动。
`ENV_FILE` 支持宿主机绝对路径；未设置时默认读取 `.env.development`。

- 附件存储根目录由 `MEDIA_ROOT` 配置，支持宿主机绝对路径，例如 `MEDIA_ROOT=/opt/dingchi-week-report/data/files`；`ATTACHMENT_UPLOAD_DIR=weekly-report` 仅表示相对于该根目录的分类子目录，最终文件落在 `/opt/dingchi-week-report/data/files/weekly-report/{report_id}/...`。
- 日志目录由 `LOG_DIR` 配置，同样支持宿主机绝对路径，例如 `LOG_DIR=/opt/dingchi-week-report/data/logs`；`LOG_FILE_NAME` 只填写文件名，日志最终写入该目录并按 `.env` 中的滚动参数轮转。

- 数据库和 Redis 连接必须使用连接池，连接池大小、超时和健康检查参数均在 `.env.*` 配置。
- MySQL 使用 `django-db-connection-pool` 的 SQLAlchemy `QueuePool` 适配器，池参数为 `MYSQL_POOL_*`；Redis 使用 `django-redis` 内置连接池。
- MySQL 使用连接池时 `MYSQL_CONN_MAX_AGE` 必须配置为 `0`。Django 只在请求结束时归还连接，底层连接仍由 QueuePool 复用；不要用 Django 持久连接时长占用池内连接槽位。
- 本地 `LOG_LEVEL=DEBUG` 时，可在请求结束后看到 `release default's connection ... to its pool` 日志，用于确认连接已归还；修改连接池配置后必须重启后端进程。
- `.env.*` 中每个配置项均保留中文用途说明；禁止把系统配置、密钥或连接参数硬编码在代码中。

## 运行时烟雾测试

后端启动后执行：

```powershell
python scripts/smoke_test.py
```

脚本会验证 `/api/v1/health/live/`，并通过统一 `/mcp/` 端点列出工具、调用 `service_health`。

AI 接口当前为本地开发示例，生产使用前需补充认证、限流和审计。
