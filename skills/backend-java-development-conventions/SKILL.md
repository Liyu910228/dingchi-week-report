---
name: backend-java-development-conventions
description: "为 Java 17+、Spring Boot/Jakarta、Maven 或 Gradle 后端新增、重构或审查代码时，应用按业务场景模块化的分层结构、API 契约、数据访问、配置、安全、可观测性、测试和依赖治理规范；不用于前端或非 JVM 服务。"
---

# Java 后端开发规范

按照项目约束完成 Java 后端服务新增、重构、缺陷修复或代码审查，使模块边界、依赖方向、运行配置、接口契约和验证结果保持一致。

## 开始前

1. 确认目标是 Java 17+ 服务；新项目优先使用当前 LTS JDK，具体版本以项目锁定的 Maven/Gradle toolchain 为准。默认适用于 Spring Boot/Jakarta、Spring MVC/WebFlux、JPA/MyBatis、MySQL/PostgreSQL、Redis 和 HTTP/JSON 服务。
2. 查找并阅读目标目录及其父目录中的 `AGENTS.md` 等项目级指令，再完整阅读 [references/backend-java-development-conventions.md](references/backend-java-development-conventions.md)。
3. 检查 `pom.xml`/`build.gradle`、wrapper、`src/main`、`src/test`、配置、数据库迁移、路由、OpenAPI 文档和运行入口；遵循已有边界，不为了“完整”创建空目录或替换既有框架。
4. 若项目提供 `docs/frontend-backend-api-conventions.md`，先按该契约实现；用户明确要求与本规范冲突时，以用户要求为准，并在交付说明中列出偏离项。
5. 明确授权范围。除非用户要求，不提交 Git、不修改外部系统、不执行生产迁移、发布、密钥轮换或删除操作。

## 不可绕过的框架约束

- 按业务场景组织 `modules/<module>/`，保持业务调用流 `controller → application → service → service/impl → dao`；Java 编译依赖中 `service/impl` 实现并依赖 `service` 接口，`application` 只依赖接口。Controller 只做协议边界，核心规则放在应用服务和 Service 实现中。内部业务模块与外部系统对接模块是同级业务场景，外部系统不得被塞入 `shared` 或全局工具包。
- `shared/utils` 只放稳定、无业务归属且确实跨模块复用的纯工具；`modules/<module>/utils` 只放本模块私有辅助代码，禁止用任一工具包绕过模块边界或堆放业务服务。
- 模块内 `beans` 是请求/响应 DTO/VO 的唯一归属；`controller` 只负责协议映射，不重复定义 DTO。外部系统模块按需增加模块私有 `client`/`adapter`，封装供应商 SDK、HTTP 和消息协议，不向其他模块泄漏。
- 使用构造器注入；禁止字段注入、静态可变状态、`System.out` 调试输出和把 JPA Entity 直接作为 API 响应。
- 所有接口定义（Java `interface`、public Service/Repository/Mapper/Port 方法和对外 HTTP 接口）都必须有注释；复杂业务逻辑、复杂 SQL 和非简单查库代码必须说明意图、约束和关键边界。
- 每个 Service 接口中的 public 方法都必须有一一对应的 JUnit 测试接口/测试类；代码改动后的默认验证只编译生产和测试源码，不运行自动化测试，除非用户明确要求或存在特殊验证要求。
- 单表读写默认使用 JPA；多表或复杂 SQL 默认使用 MyBatis Mapper + XML，SQL、参数和结果映射集中维护，不在注解或 Java 字符串中拼接复杂 SQL。Mapper/Repository 位于对应模块的 `dao`，XML 位于 `src/main/resources/mapper/<module>/`。
- 外部接口必须有版本化契约、OpenAPI 描述、边界校验、稳定错误码和统一错误响应；面向前端的 HTTP 接口只允许 GET/POST，每个查询、创建、更新、删除动作使用独立路径，不使用同一路径按不同方法承载 CRUD。
- 配置、连接池、超时、重试、日志级别、密钥和外部服务地址从环境/配置中心注入；禁止将秘密、环境专属 URL 或动态依赖版本写入代码或构建文件。
- 数据库写事务放在应用服务，迁移由 Flyway/Liquibase 等显式执行；启动、健康检查和容器入口禁止自动改表、生成迁移或生成密钥。
- 表初始化、种子数据、批量删表和批量查询脚本统一放在项目根目录 `docs/database/`，脚本必须可重复执行或明确破坏性边界，并带中文注释；表结构变化时同步更新脚本。
- 项目根目录 `docs/` 统一存放所有与代码无关的文档、SQL 脚本、契约说明和运行手册，不在源码包或页面目录散落同类文件。
- 认证授权、输入校验、输出脱敏、依赖漏洞治理和日志安全按 OWASP ASVS 选择验证级别；密码不得可逆存储或写入日志。
- 请求必须传播 trace context；日志、指标和链路数据不得包含密码、Token、Cookie、密钥、完整 Authorization Header 或敏感业务原文。

## 依赖、实现与验证

- 使用项目提供的 Maven Wrapper 或 Gradle Wrapper，锁定 JDK、插件和依赖版本；代码改动的默认本地验证只执行编译（含测试源码编译），不自动运行测试。完整质量门禁由 CI 或用户明确要求触发。
- Controller/Handler 不直接调用 Repository、JPA、Redis、HTTP SDK 或消息客户端；外部系统通过明确的 Integration/Port 适配，所有调用设置超时，重试只用于可证明安全的瞬时失败。
- REST、消息消费者、定时任务和脚本复用同一个应用服务，不复制业务规则；跨模块只依赖公开接口，不导入对方 Controller、Repository 或内部实体。
- 默认使用 JUnit Platform/Jupiter、Mockito、Spring Boot 测试切片和 Testcontainers（需要真实数据库/Redis 行为时）；测试不得依赖共享开发环境、执行顺序或真实第三方服务。

## 验证与交付

在没有特殊要求时，只按项目实际工具编译生产和测试源码，不运行自动化测试：

```text
./mvnw -B -DskipTests test-compile
./gradlew compileJava compileTestJava
```

只有用户明确要求、任务存在特殊测试条件或发布流程要求时，才额外执行自动化测试、完整质量门禁、迁移或部署检查。交付说明列出修改文件、编译命令及状态、未执行的测试/迁移/部署步骤、契约兼容性和任何规范偏离。
