# Java 后端开发约束参考

状态：强制执行
适用范围：Java 17+ 服务端新增、重构、缺陷修复和代码审查
默认技术栈：Spring Boot/Jakarta、Spring MVC 或 WebFlux、Maven 或 Gradle、JPA/MyBatis、MySQL/PostgreSQL、Redis、GET/POST HTTP/JSON API

本文中的“必须”“禁止”为强制规则；“建议”为默认做法。如项目已经锁定不同的 JDK、框架或数据访问方案，应保留项目现状并在代码评审或交付说明中说明偏离，不得静默混用两套规则。

## 1. 行业标准基线

实现和审查时优先对照以下官方规范与参考：

- [Java SE Specifications](https://docs.oracle.com/javase/specs/)：语言、虚拟机和标准库行为；生产代码不默认启用 Preview Feature。
- [Spring Boot Reference](https://docs.spring.io/spring-boot/) 与 [System Requirements](https://docs.spring.io/spring-boot/system-requirements.html)：应用装配、配置、健康检查、指标和支持的运行时边界。
- [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)：UTF-8、包/类/方法命名、导入、缩进和 100 列等可自动检查的代码风格；项目已有风格优先，但不得同时启用互相冲突的格式化器。
- 中文企业项目可参考 [Alibaba Java Coding Guidelines / P3C](https://github.com/alibaba/p3c)：命名、OOP、异常日志、单元测试、安全、MySQL 和工程结构；采用时应锁定具体版本，并将规则配置为项目唯一的企业规范来源之一。
- [OpenAPI Specification](https://spec.openapis.org/oas/)：REST 请求、响应、参数、错误和版本契约；项目应锁定使用的规范版本。
- [Jakarta Persistence](https://jakarta.ee/specifications/persistence/)：JPA 对象关系映射和持久化标准；单表操作使用 JPA 时遵循其实体、事务和查询边界。
- [MyBatis 3](https://mybatis.org/mybatis-3/)：Mapper、XML 映射、参数绑定和动态 SQL 能力；复杂多表操作按本规范默认使用 XML。
- [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html)：项目未定义统一错误包络时，使用 `application/problem+json` 表达机器可读错误；不得把堆栈当作接口错误详情。
- [Flyway](https://documentation.red-gate.com/flyway) 或 [Liquibase](https://docs.liquibase.com/)：数据库变更版本化和可审计执行；项目选择一种并保持迁移历史连续。
- [OWASP ASVS](https://owasp.org/projects/asvs)：以风险选择验证级别，普通业务默认至少评估 Level 2，高价值或高风险功能按 Level 3 评估。
- [OpenTelemetry Java](https://opentelemetry.io/docs/languages/java/)：跨线程、异步和外部调用传播 traces、metrics、logs 的上下文。
- [JUnit User Guide](https://docs.junit.org/current/user-guide/)、[Maven Build Lifecycle](https://maven.apache.org/guides/introduction/introduction-to-the-lifecycle.html)、[Gradle Wrapper](https://docs.gradle.org/current/userguide/gradle_wrapper.html)：测试平台和可复现构建入口。

这些链接用于解释规范来源，不替代项目实际锁定的版本、依赖和安全基线；升级时必须同步评估兼容性和迁移步骤。

## 2. 技术边界、目录和模块结构

### 2.1 默认目录

```text
service/
├─ pom.xml 或 build.gradle(.kts)
├─ mvnw / mvnw.cmd 或 gradlew / gradlew.bat
├─ src/
│  ├─ main/
│  │  ├─ java/com/example/service/
│  │  │  ├─ Application.java                 # 启动与装配入口
│  │  │  ├─ config/                           # Bean、配置属性、Web/安全装配
│  │  │  ├─ shared/                           # 稳定的跨领域基础设施，按需创建
│  │  │  │  └─ utils/                         # 跨模块复用的纯工具
│  │  │  ├─ security/                         # 认证、授权、脱敏、安全适配
│  │  │  ├─ observability/                    # trace、metrics、日志装配
│  │  │  └─ modules/                          # 业务场景；内部业务与外部对接同级
│  │  │     ├─ <module_A>/                    # 系统内业务场景 A
│  │  │     │  ├─ controller/                 # Controller、协议映射；不重复定义 DTO
│  │  │     │  ├─ service/                    # 业务 Service 接口
│  │  │     │  │  └─ impl/                    # Service 接口实现
│  │  │     │  ├─ dao/                        # Mapper、JPA Repository、持久化 Entity
│  │  │     │  ├─ application/                # 用例、事务、幂等和编排
│  │  │     │  ├─ beans/                      # 请求/响应 DTO、VO 的唯一归属
│  │  │     │  └─ utils/                      # 仅本模块使用的辅助工具
│  │  │     ├─ <module_B>/                    # 系统内业务场景 B，结构同上
│  │  │     └─ <integration_X>/               # 外部系统对接场景，与 module_A 平级
│  │  │        ├─ controller/                 # 回调、对账或管理接口（按需）
│  │  │        ├─ service/                    # 对接业务 Service 接口
│  │  │        │  └─ impl/                    # 对接业务实现
│  │  │        ├─ client/                     # HTTP/SDK/消息客户端适配（按需）
│  │  │        ├─ dao/                        # 本模块 Mapper/Repository/Entity（按需）
│  │  │        ├─ application/                # 对接用例、事务、幂等和编排
│  │  │        ├─ beans/                      # 本地请求/响应及映射模型
│  │  │        └─ utils/                      # 仅本模块使用的辅助工具
│  │  └─ resources/
│  │     ├─ application.yml                   # 非秘密默认配置
│  │     ├─ mapper/
│  │     │  ├─ <module_A>/                     # 对应模块的 MyBatis XML
│  │     │  │  └─ *.xml
│  │     │  └─ <integration_X>/                # 对接模块的 MyBatis XML（按需）
│  │     │     └─ *.xml
│  │     └─ db/migration/                     # Flyway/Liquibase 等运行时版本化迁移
│  └─ test/
│     ├─ java/com/example/service/
│     │  └─ modules/<module>/                  # 按生产模块镜像组织
│     │     ├─ controller/
│     │     ├─ application/
│     │     ├─ service/                        # Service 接口对应 JUnit 测试
│     │     ├─ dao/
│     │     └─ client/                         # 外部对接测试（按需）
│     └─ resources/                           # 测试配置和固定样例
├─ docs/                                      # 所有与代码无关的文档、契约和独立 SQL 脚本
│  ├─ database/
│  │  ├─ ddl/                                 # 可重复执行的表初始化 DDL
│  │  ├─ dml/                                 # 可重复执行的清表/重插入 DML
│  │  ├─ drop/                                # 带注释的批量删表脚本
│  │  └─ query/                               # 带注释的批量查询脚本
│  ├─ api/                                    # 接口契约、示例和变更说明
│  └─ runbooks/                               # 运行、排障和部署说明
└─ .github/ 或 ci/                            # CI 配置（按项目现状）
```

- 只创建实际需要的目录；禁止为了“看起来完整”创建空的 `common`、`utils`、`helpers`、`misc`、`manager` 或 `base` 包。
- `<module_A>`、`<integration_X>` 是结构占位符，不是字面包名；实际包名全部使用小写字母和数字，采用反向域名加业务场景名。类名 UpperCamelCase，方法/变量 lowerCamelCase，常量 `UPPER_SNAKE_CASE`。
- 业务场景优先于技术层平铺。内部业务场景和外部系统对接场景都直接放在 `modules/` 下；对接场景不得因为“是外部系统”就提升为全局 `integration`、`shared` 或 `utils`。外部系统的协议差异由对接模块内部吸收。
- `controller` 只负责协议、认证上下文、参数校验、DTO 映射和响应；请求/响应 DTO/VO 统一放在同一模块的 `beans`，禁止在 Controller 内重复声明。
- `service` 只声明业务能力接口，`service/impl` 实现接口并承载可复用的业务规则；`application` 编排用例、事务和幂等，不直接暴露实现细节；`dao` 只负责持久化与映射。JPA Entity 属于模块内部持久化模型，可放在 `dao/entity` 或 `dao` 子包，禁止放入 `beans` 或跨模块共享。
- 外部对接模块按需使用模块私有 `client`/`adapter` 封装 HTTP、SDK、消息和供应商模型；外部响应先转换为本地 `beans` 或内部模型，禁止把供应商类型泄漏到其他模块。
- `shared/utils` 只能放稳定、无业务归属的跨模块纯工具；模块 `utils` 只能服务当前模块。工具类不得承载业务状态、数据库访问、远程调用或通过静态全局变量保存可变状态。
- 项目根目录 `docs/` 是所有与代码无关文件的唯一归档位置，包括接口契约、设计说明、运行手册、数据库脚本和样例；不得把此类文件散落在 `src/`、业务包或任意页面目录。构建文件、运行时迁移、测试源码和实际代码仍放在各自标准目录。

### 2.2 依赖方向

```text
modules/<module>/controller → application → service 接口 → service/impl → dao
modules/<integration>/service/impl → client（外部系统适配，按需）
service/impl → service 接口；application → service 接口（实现由依赖注入绑定）
modules/<module>/* → shared/utils（仅按需使用稳定纯工具）
config/security/observability → 模块装配与横切能力（不得依赖模块内部业务实现）
shared/utils ──────────────────────────→ 不得依赖任何业务模块
```

- 上图第一行表示业务调用流；Java 编译依赖中 `service/impl` 实现并依赖 `service` 接口，`application` 只依赖接口，不得直接依赖 `impl`。依赖注入在装配阶段绑定实现。
- `controller` 只处理 HTTP/消息协议、认证上下文、边界校验、DTO 映射和响应；不得查询数据库、读写 Redis、调用第三方 SDK 或承载核心规则。
- `application` 编排一个完整用例，控制事务、幂等、权限后的业务动作和事件发布；不得依赖 Servlet、WebFlux 或具体供应商 SDK。
- `service/impl` 承载可复用业务规则，依赖本模块的 `dao`，外部对接场景还可依赖本模块 `client`；禁止反向调用 Controller 或把供应商响应对象泄漏到其他模块。
- `dao` 实现持久化、SQL、锁和映射；不得做权限、状态机或跨模块业务决策。复杂 SQL 的 XML 放在 `src/main/resources/mapper/<module>/`。
- 跨模块只依赖对方公开的 application/service 接口或明确的 `public` 契约；禁止导入对方 Controller、DAO、JPA Entity、`service/impl`、`client` 和内部配置。跨模块调用若形成环依赖，应提取稳定契约或重新划分场景。

## 3. Java 代码和 Spring 编程规范

- 源文件使用 UTF-8，一个顶层类型一个文件；每个文件包含明确的 `package` 声明，导入分组和格式化由项目统一工具执行。
- 默认使用构造器注入；禁止字段注入和在业务类中手动 `new` 受容器管理的依赖。构造器依赖过多时拆分职责，不用 Service Locator 掩盖耦合。
- DTO 优先使用不可变 `record` 或显式不可变类；JPA Entity 不直接作为请求/响应 DTO。实体的创建和修改必须保护不变量，不能用无约束的 `@Data` 覆盖整个 Entity。
- `Optional` 适合表达返回值可能缺失，不用于字段、序列化 DTO、方法参数或集合元素；对可空输入使用显式校验和清晰的空值策略。
- 不使用 `System.out`、`System.err`、空 `catch`、无说明的 `TODO`、裸 `RuntimeException` 或吞异常；统一使用 SLF4J/项目日志门面和稳定异常层级。
- 不依赖 Preview Feature、反射扫描或代码生成隐藏核心规则；必须使用时在构建、运行时和迁移说明中明确版本与回退方案。
- 按 Google Java Style、Alibaba P3C 或项目已配置的等价格式化器执行 UTF-8、缩进、列宽、命名和导入规则；同一项目必须选定并自动化一套主规则，禁止同时启用互相冲突的格式化器或让个人 IDE 格式覆盖仓库格式。
- 所有接口定义必须写注释：包括 Java `interface`、public Service/Repository/Mapper/Port 方法、Controller/Handler 对外方法、消息消费者入口和公开配置扩展点。注释至少说明职责、参数、返回值、异常/错误码、事务或幂等要求及线程/资源边界。
- 复杂逻辑必须写注释说明“为什么这样做”和关键不变量，包括状态机、权限/幂等判断、批量处理、并发控制、复杂 SQL、外部重试和数据转换；简单 getter、单表直查和显而易见的语句不需要逐行注释。注释不得只复述代码，也不得保留无上下文的 TODO。
- Spring Bean 只做清晰职责；`@RestController`、`@Service`、`@Repository`、`@Configuration` 的边界要与包结构一致，不用注解堆叠替代分层设计。

## 4. 构建、依赖和供应链

- 所有构建必须通过仓库提交的 Maven Wrapper 或 Gradle Wrapper；CI、开发机和容器使用同一 wrapper 版本与 JDK toolchain。
- Maven 使用 parent/BOM 统一版本，Gradle 使用 version catalog/platform/BOM；禁止在多个模块重复声明同一依赖版本。
- 禁止使用无边界的版本范围、默认拉取最新版本或在生产构建中依赖未锁定的 `SNAPSHOT`。升级依赖必须记录兼容性、漏洞影响和回滚方案。
- 构建配置应支持编译、单元测试、格式/静态检查、打包和依赖安全检查；适合时生成 SBOM，并将依赖漏洞扫描纳入 CI，而不是只在本地运行。
- 本规范默认的代码改动验证只编译生产和测试源码，不执行自动化测试：Maven 使用 `./mvnw -B -DskipTests test-compile`，Gradle 使用 `./gradlew compileJava compileTestJava`。只有用户明确要求、任务存在特殊测试条件或发布流程要求时，才执行 `verify`/`check` 和测试。
- 不得把默认不运行测试误解为删除测试或掩盖失败；测试接口/测试类仍必须提交并保证能编译。明确要求执行测试时，不得用 `-DskipTests`、排除规则或关闭插件绕过失败。
- 多模块只在确有边界和独立发布需求时使用；模块之间通过公开 API/Port 依赖，禁止循环依赖和靠大规模 re-export 隐藏依赖。
- 构建脚本不得包含密钥、私有仓库密码、生产地址或破坏性发布命令；凭据通过 CI secret、环境变量或受控凭据插件注入。

## 5. Web/API 层与契约

### 5.1 前端 HTTP API 基本约束

- 本节的 `GET`/`POST` 限制只针对前端交互接口。外部系统出站调用、供应商回调和消息协议按对方已发布契约实现，即使对方要求其他 HTTP 方法也必须隔离在对应对接模块的 `client`/`controller` 内，并记录契约、认证、超时、重试和幂等策略。
- 所有与前端交互的 HTTP API 只允许使用 `GET` 和 `POST`：查询使用 `GET`，创建、更新、删除和其他改变状态的操作使用 `POST`。禁止使用 `PUT`、`PATCH`、`DELETE` 实现前端 CRUD。
- 前端接口不采用标准 RESTful 的同一路径多方法模式；每个动作必须使用独立、可读、版本化的路径，例如 `GET /api/v1/reports/list`、`POST /api/v1/reports/create`、`POST /api/v1/reports/update`、`POST /api/v1/reports/delete`。禁止同一个 API 路径根据请求方法不同实现增改查删。
- 前端 HTTP API 默认从 `/api/v1/` 进入，路径使用稳定的小写动作/业务名；方法、状态码、幂等性、分页、排序、过滤、缓存和内容类型必须写入 OpenAPI 契约。
- 请求边界使用 `jakarta.validation`（如 `@Valid`、`@NotNull`、长度/范围/枚举校验）做结构校验；跨字段和业务约束放到 application/service，不能只依赖注解。
- Controller 方法必须有中文契约注释，至少说明用途、方法/路径、认证权限、幂等要求、请求字段和类型、成功响应、错误码、`trace_id`、脱敏和兼容策略。
- API 层只返回稳定的 DTO/JSON；禁止直接序列化 Entity、`Page` 内部结构、异常、SQL、第三方响应、堆栈或数据库字段。
- 成功和失败包络必须遵循项目 API 契约。若项目未定义包络，错误优先使用 RFC 9457 的 `application/problem+json`；同一路由不得混用多种格式。
- `@RestControllerAdvice` 或等价统一异常映射负责状态码、错误码、客户端安全文案和 trace ID；未知异常对外只返回通用错误，对内记录受控堆栈。

### 5.2 本仓库前后端契约

如果目标项目提供 `docs/frontend-backend-api-conventions.md`，以下规则必须与其保持一致：

- 成功使用 `success: true`，失败使用 `success: false`、稳定 `error.code` 和 `trace_id`；响应头传播 `X-Trace-ID`。
- 64 位 Snowflake ID 在 JSON 中始终作为字符串；日期时间使用带时区的 ISO 8601；字段和枚举遵循约定的 `snake_case`；金额、数量、时长标明单位；分页字段保持统一。
- 每个请求函数、Controller 或消息入口都要给出中文契约注释和示例；接口变更先改契约，再同步实现、客户端类型、契约测试和兼容性说明。
- 前端密码若按现有契约使用 `RSA-OAEP-SHA256` 传输，Java 端必须复用统一的公钥、解密、字段版本和脱敏策略；不得在其他接口另起一套加密方式，也不得把密码明文写入日志或响应。

## 6. 认证、授权和应用安全

- 默认拒绝未认证请求；认证负责建立身份上下文，授权由 Spring Security/Policy/应用服务按资源和动作判断。认证失败与权限不足分别使用 401/403。
- 对浏览器会话正确处理 CSRF、SameSite、Cookie Secure/HttpOnly；CORS 使用明确 allowlist，禁止生产 `*` 配合凭据。OAuth2/OIDC、JWT、API Key 等方案必须记录签发方、受众、过期、轮换和撤销策略。
- 密码使用 Argon2id、bcrypt 等单向密码哈希并带唯一盐；禁止可逆保存、日志记录、URL 传输和自定义密码算法。客户端额外加密不能替代 TLS 和服务端密码哈希。
- 所有输入按上下文校验/编码；SQL 使用参数绑定；文件上传校验类型、大小、扩展名和存储路径；SSRF、命令执行、模板注入、反序列化和路径穿越使用 allowlist/安全 API 防护。
- 不对不可信数据使用原生 Java 序列化；JSON 多态反序列化必须使用白名单类型和安全配置。
- 依赖、容器镜像和构建插件执行漏洞扫描；高危漏洞必须有升级、缓解或风险接受记录。安全需求按 OWASP ASVS 版本化引用，例如 `v5.0.0-...`，不要只写“符合 ASVS”。
- 生产必须使用 HTTPS/TLS；密钥、Token、私钥、数据库密码和第三方凭据只来自 secret manager/环境注入，禁止提交 Git、写入镜像层或打印配置全量。

## 7. 数据库、缓存和事务

- 业务事实以关系数据库为准；单表增删改查默认使用 JPA/Hibernate Repository。多表操作、复杂报表、聚合查询、性能敏感查询和需要明确 SQL 的场景默认使用 MyBatis Mapper + XML，SQL、参数和结果映射集中在对应模块的 `modules/<module>/dao/` 与 `src/main/resources/mapper/<module>/`，不得把复杂 SQL 写在注解或 Java 字符串中。
- MyBatis XML 必须使用参数绑定和明确的 `resultMap`/结果类型；动态条件采用受控白名单，禁止拼接用户输入、表名、列名或排序片段。每个复杂查询说明用途、关联关系、分页/锁策略和索引假设。
- Repository/DAO 负责持久化、查询、锁和映射，不做权限、状态机或跨实体业务决策；禁止 Controller/Service 直接拼 SQL 或依赖 ORM Entity 的懒加载副作用。
- Schema 变更必须使用 Flyway、Liquibase 或项目约定的版本化迁移；生产禁用自动建表/更新。启动、健康检查和容器入口不得自动执行迁移、生成表或生成密钥。
- `@Transactional` 放在 application 层的用例边界；事务内不执行远程 HTTP、AI、消息等待或长时间文件操作。写入流程明确隔离级别、锁策略、幂等和重试边界。
- 分页有上限，批量读取/写入必须分批；审查 N+1、笛卡尔积、全表扫描、慢查询和连接泄漏。需要并发更新时使用乐观锁/版本号或明确锁策略。
- 数据库使用 HikariCP 等连接池，连接数、超时、健康检查和泄漏检测从配置注入；禁止每请求新建连接或在业务代码中关闭共享池。
- Redis 只做缓存、锁、限流和临时状态，不能作为业务事实唯一来源；Key 包含应用、环境、领域、用途、标识和版本，所有缓存必须有 TTL、失效和击穿策略。Redis 客户端复用连接池/共享客户端。
- 若目标项目沿用本仓库现有数据规范，表关联使用明确的逻辑 `*_id` 或中间表，禁止在 ORM 中隐式跨模块关联；如果项目 schema 明确允许数据库外键，则以 schema owner 的约束为准并记录理由。

### 7.1 数据库脚本交付

- 表初始化 DDL 统一放在 `docs/database/ddl/`，必须可重复执行：使用幂等的建表、字段、索引和基础对象判断；每张表、字段、索引和关键约束都要有中文注释。生产版本迁移仍由 `src/main/resources/db/migration/` 的 Flyway/Liquibase 版本脚本负责，不能用初始化脚本替代迁移历史。
- 初始化/种子 DML 统一放在 `docs/database/dml/`，必须支持重复执行：先按明确顺序清表，再插入完整数据；脚本应放在事务中或说明数据库限制、清理顺序、唯一键和环境范围。清表重插入脚本只用于开发、测试、演示或用户明确授权的环境，禁止默认对生产执行。
- 批量删表脚本统一放在 `docs/database/drop/`，必须带中文注释、依赖顺序和明确的破坏性警告；需要时加入环境确认/事务边界，禁止在应用启动、健康检查或普通部署命令中自动执行。
- 批量查询脚本统一放在 `docs/database/query/`，每条查询都要有中文注释、用途、参数说明、关联范围、分页/上限和敏感字段提示；禁止默认执行无条件全表扫描或输出密码、Token 等敏感数据。
- 表结构、字段、索引、初始数据或查询语义发生变化时，必须同时更新对应 DDL、DML、drop、query 脚本、运行时迁移和文档；交付说明列出脚本是否执行。

## 8. 配置、启动和运行边界

- 配置使用 `@ConfigurationProperties` 或等价类型化绑定集中管理；不要在各类中散落 `@Value`、环境读取或默认秘密。缺少必填配置必须启动失败。
- `application.yml` 只放安全默认值和非秘密模板；环境地址、端口、池大小、超时、重试、日志、CORS、认证、AI 模型和开关通过 profile/环境/配置中心注入，并同步 `.env.example` 或部署模板。
- 应提供健康检查、优雅停机、readiness/liveness 区分和启动失败诊断；健康检查不得执行破坏性写入、迁移、密钥生成或深度业务查询。
- 定时任务、消息消费者和命令行脚本显式启动，必须有幂等、并发控制、失败重试/死信和关闭策略；不能在类加载或 Spring Bean 构造器里启动后台线程。
- 外部 HTTP/消息/文件系统调用必须配置连接、读取和整体超时；重试只用于瞬时且幂等的操作，使用指数退避和抖动，避免无限重试和级联故障。

## 9. 追踪、日志、指标和异常

- 使用 OpenTelemetry Java Agent/SDK、Spring/Micrometer 集成或项目等价方案传播 W3C trace context；入口缺失/非法 trace ID 时生成，响应、日志和下游调用复用同一上下文。
- 日志使用 SLF4J/Logback 等统一门面，生产优先结构化 JSON；日志至少包含时间、级别、logger、trace ID、动作和结果，异常堆栈只在服务端受控记录。
- 禁止记录密码、RSA 密文、私钥、公钥文件内容、Token、Cookie、完整 Authorization Header、数据库连接串、完整 Prompt 和敏感业务原文；路径、query、请求体和异常 message 也要按敏感字段审查。
- 指标使用低基数标签，避免把 user ID、订单号、URL 原始参数等高基数字段作为 label；至少覆盖请求量、延迟、错误率、数据库连接池、缓存和外部依赖。
- 统一异常层只映射可预期错误；不要 catch 后继续返回成功，也不要把 `Exception.getMessage()` 原样返回客户端。跨线程/异步任务必须观察和处理异常结果。

## 10. 并发、异步和外部集成

- 每个有独立业务目标、数据映射、状态机、重试或幂等边界的外部系统对接，作为 `modules/` 下的独立业务场景，与内部业务模块平级；不要把多个对接方合并成一个无边界的全局 Integration 包。
- 不在业务代码创建无界线程池、裸线程或共享可变静态集合；线程池、队列容量、拒绝策略和关闭动作必须可配置且可观测。
- WebFlux/响应式线程上禁止同步 ORM、阻塞文件 I/O 和阻塞 SDK；若必须阻塞，明确切换到隔离调度器并限制并发。Servlet 模型也要避免长时间占用请求线程。
- Java 21 虚拟线程可用于明确评估过的阻塞 I/O 场景，但不得把它作为无限并发的替代品；仍需限制下游连接池、队列和请求超时。
- CompletableFuture、消息 ack、定时任务和异步事件必须传播 trace/security context，处理取消、超时、异常和重复投递；不能 fire-and-forget 丢失失败。
- 外部客户端封装在对应 `modules/<integration>/client` 或模块私有 Adapter，定义本地请求/响应类型和稳定异常；禁止把供应商 SDK 类型传入其他模块、Service 公共接口或 API 层。外部对接场景与系统内业务场景同属 `modules/`，不得把单个供应商客户端提升为全局共享能力。
- 对创建/扣款/发送等副作用接口使用幂等键、去重表或业务唯一约束；重试前确认操作是否真正幂等。

## 11. 数据类型和序列化

- API 时间使用 UTC 的 `Instant` 或带时区的 `OffsetDateTime`，明确精度和时区策略；数据库时间映射必须一致，禁止用无时区 `LocalDateTime` 表示跨地域事件。
- 金额使用 `BigDecimal` 和明确的货币/小数位；数量、比例和时长写明单位，禁止用浮点数承载金额或关键计量。
- 对外 ID 按 API 契约决定；若使用 64 位 Snowflake，JSON 用字符串避免 JavaScript 精度损失。枚举对外使用稳定值，不直接暴露 Java 常量名或 ordinal。
- DTO/事件版本需要兼容未知字段；禁止把数据库 Entity、异常、`Page`、`Optional` 或延迟代理直接序列化。
- 显式定义 null、缺省、空列表和分页语义；不要用隐式 `null` 代表多个业务状态。

## 12. 测试、静态检查和质量门禁

### 12.1 测试边界

- 每个 Service 接口中的 public 方法都必须归入一一对应的 JUnit 测试接口/测试类，命名默认使用 `<ServiceName>Test` 或 `<ServiceName>ContractTest`；接口包含多个实现时，用共享契约测试覆盖公共行为，并为每个实现提供适配测试。
- Service 测试至少为每个 public 方法定义正常、边界和失败行为的测试用例或明确的契约测试占位；测试必须提交并可编译，但在没有特殊要求时不自动执行。
- 单元测试覆盖 application/service 的规则、状态转换、事务分支、幂等和错误映射；使用 JUnit Jupiter/JUnit Platform、Mockito 或项目现有替身。
- Web 层使用 Spring Boot 测试切片或 MockMvc/WebTestClient，覆盖认证、权限、参数校验、响应包络、错误码和 trace ID；不要每个单测都启动完整容器。
- Repository/数据库/Redis 行为使用 Testcontainers 或项目隔离的容器环境；不要依赖共享开发数据库、真实生产数据、固定执行顺序或真实第三方。
- Integration/Contract 测试覆盖 OpenAPI/JSON、消息 schema、超时、重试、幂等和版本兼容；外部服务用 WireMock/MockServer/Fake 等隔离。
- 注入 `Clock`、ID 生成器和随机源以保证时间、ID 和重试测试可重复；并发测试必须有明确的等待/超时和清理。
- 需要时用 ArchUnit/依赖分析测试验证包依赖方向；覆盖率用于发现风险，不得通过删除断言或只测 getter 达标。

### 12.2 标准验证命令

按仓库实际构建工具执行，不要同时引入两套命令：

```text
# Maven
./mvnw -B -DskipTests test-compile

# Gradle
./gradlew compileJava compileTestJava
```

以上命令只编译生产和测试源码，不运行自动化测试。只有用户明确要求、任务存在特殊测试条件或发布流程要求时，才追加 `verify`/`check`、测试、启动/健康检查、契约测试、数据库迁移校验和容器镜像扫描。涉及前端联调时，再执行前端规定的类型检查和构建。无法运行的检查必须说明原因。

## 13. 新功能实施流程

1. 读取 `AGENTS.md`、本参考、构建文件、API/消息契约和运行配置。
2. 明确 JDK、Spring/ Jakarta、Maven/Gradle、数据库、缓存、部署和兼容性边界。
3. 先更新 OpenAPI/消息 schema、所有接口定义的中文注释、错误码、示例和迁移设计。
4. 按业务场景创建 `modules/<module>/controller`、`application`、`service`、`service/impl`、`dao`、`beans`、`utils` 中实际需要的包；外部对接场景按需增加模块私有 `client`/`adapter`，不创建空层。
5. 实现输入校验、认证授权、应用用例、事务/幂等和统一响应；保持 `controller → application → service → service/impl → dao` 依赖方向，并为所有接口和复杂逻辑补充注释。
6. 单表操作使用 JPA；多表/复杂 SQL 使用对应模块的 MyBatis XML；添加 Repository/Mapper、外部对接模块的 client/adapter、连接池、超时、重试、日志、trace、metrics 和配置绑定。
7. 添加版本化数据库迁移及 `docs/database/` 下可重复执行的 DDL、清表重插入 DML、批量删表和带注释查询脚本；确认启动和健康检查不会自动执行迁移或生成秘密。
8. 为每个 public Service 接口创建对应 JUnit 测试接口/测试类，并补充 Web、Repository/容器、契约和安全相关测试；检查 N+1、敏感日志和错误泄露。
9. 默认只运行 wrapper 的生产/测试源码编译，不运行自动化测试；只有特殊要求时才执行完整验证、依赖漏洞扫描和容器/健康检查。
10. 交付时列出变更文件、编译命令和状态、未执行的测试/迁移/部署、API 兼容性和偏离规范的理由。

## 14. 完成定义

新功能只有同时满足以下条件才算完成：

- [ ] JDK、wrapper、框架和依赖版本已锁定，未使用无边界版本或未说明的 Preview Feature。
- [ ] 包按业务场景组织在 `modules/` 下；内部业务与外部对接场景平级，依赖方向为 `controller → application → service → service/impl → dao`，实现与接口依赖清晰，无循环依赖和跨模块内部导入。
- [ ] Controller/Handler 没有 ORM、SQL、Redis、外部 SDK 或核心业务规则；使用构造器注入，不使用字段注入。
- [ ] 所有 Java interface、public Service/Repository/Mapper/Port 方法和对外入口都有职责、参数、返回值、错误/资源边界注释；复杂逻辑和复杂 SQL 有说明意图与关键不变量的注释。
- [ ] 每个 Service 接口中的 public 方法都有对应的 JUnit 测试接口/测试类，测试源码已提交并可编译。
- [ ] 请求/响应 DTO 与 Entity 分离，边界校验、认证授权、统一错误映射和中文契约注释完整。
- [ ] 面向前端的接口只使用 GET/POST；查询、创建、更新、删除使用独立路径，没有同一路径按请求方法复用 CRUD。
- [ ] OpenAPI/消息契约、成功/错误 JSON、状态码、分页、ID、日期、单位、trace ID 和兼容性策略一致。
- [ ] 单表操作默认使用 JPA，多表/复杂 SQL 默认使用对应模块的 MyBatis XML；查询已审查 N+1、分页、锁和连接池；事务位于 application 层。
- [ ] Schema 迁移已版本化，启动/健康检查/容器入口不会自动改表或生成密钥。
- [ ] `docs/` 统一存放代码无关文件；`docs/database/` 已提供可重复执行 DDL、清表重插入 DML、带警告的批量删表和带注释的批量查询脚本，表结构变化已同步更新。
- [ ] 配置类型化且外置，秘密没有进入源码、构建文件、镜像、日志、URL 或响应。
- [ ] 认证、授权、CSRF/CORS/TLS、输入校验、输出脱敏和依赖漏洞按适用的 OWASP ASVS 级别验证。
- [ ] 请求、异步任务和下游调用传播 trace context；日志无敏感数据，指标没有无界高基数标签。
- [ ] 超时、重试、幂等、断路/隔离和关闭策略已针对外部调用明确配置。
- [ ] JUnit/Web/Repository/契约/安全测试覆盖关键路径，外部依赖隔离，测试不依赖共享环境。
- [ ] 默认已执行 `./mvnw -B -DskipTests test-compile` 或 `./gradlew compileJava compileTestJava`，生产与测试源码编译通过；未在无特殊要求时自动运行测试。
- [ ] 如用户或发布流程明确要求自动化测试、完整质量门禁或扫描，已额外执行并报告结果；否则已明确列出未执行项。
- [ ] 未执行用户未授权的迁移、部署、发布、密钥轮换或 Git 操作。
