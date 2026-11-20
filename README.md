# 鼎驰周报本地开发项目

本目录包含相互独立的前端、后端和本地基础设施配置，不需要初始化或提交 Git。

## 目录

- `frontend/`：Vue 3、Vite 6、Vue Router、Pinia、Axios、TypeScript。
- `backend/`：Python 3.12+、Django 6、MCP 2、OpenAI-compatible SDK、MySQL、Redis。
- `docker-compose.yml`：本地 MySQL 8.4 与 Redis 7.4。

前后端对接统一遵循 [API 对接规范](docs/frontend-backend-api-conventions.md)：接口是唯一边界，双方只按
版本化 JSON 契约协作；每个接口必须提供中文用途、请求参数、响应数据和错误码说明。

后端框架已内置统一 `X-Trace-ID` 请求追踪、`.env.*` 驱动的滚动日志、雪花主键工具和
RSA-OAEP-SHA256 密码传输/存储工具。首次使用后端时，在 `backend/` 下显式执行
`python scripts/generate_crypto_keys.py` 生成本地密钥；项目启动不会自动生成密钥或执行数据库迁移。

## 本地启动

### 1. 启动 MySQL 和 Redis

在项目根目录执行（配置从 `backend/.env.development` 注入）：

```powershell
docker compose --env-file backend/.env.development up -d mysql redis
```

如果本机已经有 MySQL/Redis，可直接修改 `backend/.env.development` 的连接信息。

当前本地配置按现有服务填写：MySQL `root / aa-123456`，Redis URL 使用
`redis://:aa-123456@127.0.0.1:6379/0`。如果 Redis 实例未启用密码，请删除 URL 中的密码段。

### 2. 启动后端

```powershell
cd backend
python -m venv .venv
./.venv/Scripts/Activate.ps1
python -m pip install -e ".[dev]"
python -m uvicorn config.asgi:application --reload --host 127.0.0.1 --port 8000
```

```cmd
cd backend
.venv\Scripts\python.exe -m uvicorn config.asgi:application --reload --port 8000
```

项目启动不会自动执行数据库迁移。需要变更数据库结构时，单独审核并手动执行：

```powershell
cd backend
python manage.py makemigrations
python manage.py migrate --plan
python manage.py migrate
```

首次初始化系统配置种子（项目启动不会自动执行；不会写入周报、月度计划等业务数据）：

```powershell
mysql -uroot -p dingchi_week_report < "docs/数据库脚本/02_初始化DML.sql"
```

演示账号密码统一为 `aa123456`：`delivery.specialist`、`delivery.assistant`、`recruiter`、
`delivery.manager`、`recruitment.manager`、`ito.sales`、`innovation.sales`、`president`、`admin`。
总裁账号同时拥有总裁和系统管理员角色，可在页面右上角切换。

必须使用 ASGI 命令启动，MCP 的 Streamable HTTP 生命周期才会同时运行。后端入口：

- API 索引：`http://127.0.0.1:8000/api/v1/`
- 存活检查：`http://127.0.0.1:8000/api/v1/health/live/`
- 就绪检查：`http://127.0.0.1:8000/api/v1/health/ready/`
- AI 对话：`POST http://127.0.0.1:8000/api/v1/ai/chat/`
- MCP：`http://127.0.0.1:8000/mcp/`
- 加密公钥：`http://127.0.0.1:8000/api/v1/security/public-key/`

### 3. 配置大模型

编辑 `backend/.env.development`：

```dotenv
AI_API_KEY=your-api-key
AI_BASE_URL=https://your-provider.example/v1
AI_MODEL=your-model-name
```

`AI_BASE_URL` 留空时使用 OpenAI SDK 默认地址；也可以填写兼容 OpenAI Chat Completions 的服务地址。

### 4. 启动前端

打开另一个 PowerShell：

```powershell
cd frontend
npm install
npm run dev
```

访问 `http://127.0.0.1:5173`。Vite 会把 `/api` 请求代理到 `http://127.0.0.1:8000`。

## 校验

```powershell
cd frontend
npm run type-check
npm run build

cd ../backend
python manage.py check --settings=config.settings.test
python manage.py test --settings=config.settings.test
# 后端启动后，还可执行：python scripts/smoke_test.py
```

后端运行时还可在 `backend/` 下执行 `python scripts/smoke_test.py`，同时检查真实的 API 与 MCP HTTP 通路。

## 分层约定

前端按 `app → views/layouts → features → shared` 分层；后端按 `config → apps` 分层，业务模块内部使用 `views → services → dao/integrations`，所有 MCP 工具统一位于 `apps/mcp_server/modules/<capability>/`。新增业务时优先创建独立 feature/app，不把领域逻辑堆在路由或视图函数中。




本地测试账号：
username	        display_name    password
admin	            系统管理员       Worker@123

president	        周总

recruitment.manager	李四
recruiter	        林晓

delivery.manager	张三
delivery.specialist	陈默
delivery.assistant	王助理

ito.sales	        张销售
innovation.sales	李销售

functional.group    职能组
## AI 助手与语义层（Auto-Ontology vendor 集成）

后端内置两类数据查询能力，均通过 `/api/v1/ai/chat/` 的 function calling 提供：

| 能力 | 模块 | 适用场景 |
|------|------|----------|
| 个人/团队数据工具（7 个中的 6 个） | `apps/ai_gateway/services/user_data_tools.py` | 我的信息、我的月报/周报、共享月报、团队月报/周报（领导） |
| 语义层开放统计（`query_weekly_data`） | `apps/ontology/` + `backend/vendor/auto_ontology/` | 排名、分布、跨表统计等自由分析 |

**权限原则：AI 的数据权限 = 当前登录用户本人的系统权限**（self 仅本人 / team 团队+本人 / all 全部）。
语义层由 `apps/ontology/guard.py` 在 connector 层用 sqlglot 改写 SQL 实现行级隔离：
员工维度表在表读取层注入 `employee_id IN (可见范围)`，仅允许单条 SELECT、禁写、自动 LIMIT。

### 部署语义层（可选，不部署则仅 query_weekly_data 不可用）

1. 启动 postgres+pgvector 容器并准备语义元数据库（库名 `auto_ontology`，含术语/列属性向量表）。
2. 在 `backend/.env.*` 配置 `ONTOLOGY_PG_*`（见 `.env.example` 第 12 节）；
   LLM/Embedding 复用 `AI_API_KEY`/`AI_BASE_URL`/`AI_MODEL`，由 `apps/ontology/services.py` 自动映射。
3. 追加安装语义层依赖（注意：会把 openai 固定到 2.54.0，为实测兼容组合）：

   ```bash
   uv pip install --python .venv/bin/python -r requirements-ontology.txt
   ```

4. 语义元数据初始化：使用 NVIDIA Auto-Ontology 官方服务对业务 MySQL 做 ingestion + 语义编译，
   完成后即可停掉官方服务，Django 进程独立使用编译结果。

### 管理员模型配置

系统管理员可在「系统设置 → 模型配置」维护主模型、视觉模型、Base URL 和 API Key，
并在保存前直接测试当前表单中的模型连通性。配置保存在 `ai_model_config` 表并即时生效，
无需重启；环境变量仅作为首次配置前的初始值。API Key 使用系统 RSA 字段加密存储，接口只返回掩码。
视觉模型用于先把图片整理为文字笔记，再交给主模型生成内容；当前千问服务实测使用 `qwen3-vl-plus`。

### AI 助手图片与文件写作

AI 助手支持每条消息最多 4 个附件、单文件最大 10MB：
PNG/JPEG/WebP/GIF、PDF、DOCX、XLSX、TXT、MD、CSV、JSON。
上传接口为 `POST /api/v1/ai/attachments/`，聊天消息的 `attachment_ids` 引用附件；
历史消息保留引用后可继续追问。附件只存放在私有媒体目录并校验上传者所有权，不提供公开文件 URL。

可根据附件直接生成周报或月度计划草稿。附件内容仅作为写作素材，缺失日期、负责人或交付物应标为待确认；
生成结果不会自动保存或提交到周报/月报业务表。
