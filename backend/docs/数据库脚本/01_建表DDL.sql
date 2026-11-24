-- DingChi 周报系统 MySQL 建表脚本
-- 版本：与当前 Django 模型及内置组件同步（2026-11-24，ai_gateway 0001~0004 / weekly_report 0024）
--
-- 使用说明：
-- 1. 本脚本只负责创建当前项目已知表，不创建数据库、不执行迁移。
-- 2. 所有 CREATE TABLE 均使用 IF NOT EXISTS；已有表不会被修改。
--    存量库按缺失表逐张执行对应 CREATE TABLE 语句，不能仅重跑本文件。
-- 3. 业务表的关联字段均为逻辑 BIGINT ID，不创建外键；Django 框架表的外键
--    是框架自身权限/后台功能所需约束，不属于业务表关联。
-- 4. 业务主键由应用层雪花算法生成；日期时间统一使用 DATETIME(6)，不使用 BIGINT。

SET NAMES utf8mb4;

-- =========================
-- 业务表
-- =========================

CREATE TABLE IF NOT EXISTS `system_dictionary` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `dict_type` VARCHAR(64) NOT NULL COMMENT '字典类型编码',
    `dict_code` VARCHAR(64) NOT NULL COMMENT '字典项编码',
    `dict_name` VARCHAR(128) NOT NULL COMMENT '字典项名称',
    `dict_value` VARCHAR(255) NOT NULL COMMENT '字典项实际值',
    `description` VARCHAR(255) NOT NULL COMMENT '字典项说明',
    `status` VARCHAR(16) NOT NULL COMMENT '状态：active启用、inactive停用',
    `sort_order` INT UNSIGNED NOT NULL COMMENT '同类型字典项排序号',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_system_dictionary_type_code` (`dict_type`, `dict_code`),
    KEY `idx_system_dictionary_lookup` (`dict_type`, `status`, `sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统静态字典表';

CREATE TABLE IF NOT EXISTS `organization_group` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `group_code` VARCHAR(64) NOT NULL COMMENT '组织分组编码',
    `group_name` VARCHAR(128) NOT NULL COMMENT '组织分组名称',
    `description` VARCHAR(255) NOT NULL COMMENT '分组说明',
    `parent_group_id` BIGINT NULL COMMENT '父分组ID，逻辑关联 organization_group.id',
    `is_system` BOOL NOT NULL DEFAULT 0 COMMENT '是否为系统预设分组：1是、0否；预设分组不可删除',
    `status` VARCHAR(16) NOT NULL COMMENT '状态：active启用、inactive停用',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_organization_group_group_code` (`group_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='组织分组表';

CREATE TABLE IF NOT EXISTS `role` (
    `deletion_key` BIGINT NOT NULL DEFAULT 0 COMMENT '未删除为0，软删除为本记录ID',
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `role_code` VARCHAR(64) NOT NULL COMMENT '角色编码',
    `role_name` VARCHAR(128) NOT NULL COMMENT '角色名称',
    `scope` VARCHAR(16) NOT NULL COMMENT '数据范围编码，关联 system_dictionary.role_scope',
    `description` VARCHAR(255) NOT NULL COMMENT '角色说明',
    `report_template_code` VARCHAR(64) NOT NULL COMMENT '周报模板编码，关联 system_dictionary.report_template',
    `role_group_code` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '角色分组编码，逻辑关联 organization_group.group_code',
    `status` VARCHAR(16) NOT NULL COMMENT '状态：active启用、inactive停用',
    `sort_order` INT UNSIGNED NOT NULL COMMENT '角色显示排序号',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_role_code_live` (`role_code`, `deletion_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统角色表';

CREATE TABLE IF NOT EXISTS `user_account` (
    `deletion_key` BIGINT NOT NULL DEFAULT 0 COMMENT '未删除为0，软删除为本记录ID',
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `username` VARCHAR(64) NOT NULL COMMENT '登录用户名',
    `employee_no` VARCHAR(64) NOT NULL COMMENT '员工工号',
    `display_name` VARCHAR(128) NOT NULL COMMENT '员工显示姓名',
    `email` VARCHAR(254) NOT NULL COMMENT '员工邮箱',
    `phone` VARCHAR(32) NOT NULL DEFAULT '' COMMENT '员工手机号',
    `password_ciphertext` LONGTEXT NOT NULL COMMENT '非对称加密后的密码密文',
    `manager_id` BIGINT NULL COMMENT '直属上级用户ID，逻辑关联 user_account.id',
    `group_id` BIGINT NULL COMMENT '主组织分组ID，逻辑关联 organization_group.id',
    `avatar_color` VARCHAR(16) NOT NULL COMMENT '头像背景色',
    `status` VARCHAR(16) NOT NULL COMMENT '状态：active启用、inactive停用',
    `is_super` BOOL NOT NULL DEFAULT 0 COMMENT '是否为超级管理员：1是、0否；仅通过数据库维护',
    `last_login_at` DATETIME(6) NULL COMMENT '最近登录时间',
    `mcp_api_key` VARCHAR(255) NULL COMMENT 'MCP 接口调用密钥，用于按密钥定位调用用户并判定数据范围',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_user_username_live` (`username`, `deletion_key`),
    UNIQUE KEY `uq_user_account_employee_no` (`employee_no`),
    UNIQUE KEY `uq_user_account_mcp_api_key` (`mcp_api_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户账号表';

CREATE TABLE IF NOT EXISTS `user_role` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID，逻辑关联 user_account.id',
    `role_id` BIGINT NOT NULL COMMENT '角色ID，逻辑关联 role.id',
    `is_default` BOOL NOT NULL COMMENT '是否为用户默认角色：1是、0否',
    `status` VARCHAR(16) NOT NULL COMMENT '状态：active启用、inactive停用',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_user_role_pair` (`user_id`, `role_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';

CREATE TABLE IF NOT EXISTS `user_group_membership` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID，逻辑关联 user_account.id',
    `group_id` BIGINT NOT NULL COMMENT '组织分组ID，逻辑关联 organization_group.id',
    `is_primary` BOOL NOT NULL COMMENT '是否为用户主分组：1是、0否',
    `status` VARCHAR(16) NOT NULL COMMENT '状态：active启用、inactive停用',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_user_group_pair` (`user_id`, `group_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户组织分组关联表';

CREATE TABLE IF NOT EXISTS `report_template` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `template_code` VARCHAR(64) NOT NULL COMMENT '周报模板唯一编码（编码中包含版本号，例如 delivery_assistant_v1）',
    `template_name` VARCHAR(128) NOT NULL COMMENT '模板名称',
    `description` VARCHAR(500) NOT NULL COMMENT '模板说明',
    `status` VARCHAR(16) NOT NULL COMMENT '状态：active启用、inactive停用',
    `effective_from` DATE NULL COMMENT '生效开始日期',
    `effective_to` DATE NULL COMMENT '生效结束日期',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_report_template_code` (`template_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='周报模板主表';

CREATE TABLE IF NOT EXISTS `report_template_item` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `template_id` BIGINT NOT NULL COMMENT '模板ID，逻辑关联 report_template.id',
    `section_code` VARCHAR(64) NOT NULL COMMENT '模板分区编码',
    `section_name` VARCHAR(128) NOT NULL COMMENT '模板分区名称',
    `task_code` VARCHAR(64) NOT NULL COMMENT '模板任务项编码',
    `label` VARCHAR(255) NOT NULL COMMENT '任务项标题',
    `guidance` VARCHAR(500) NOT NULL COMMENT '填写指引',
    `item_type` VARCHAR(16) NOT NULL COMMENT '项目类型',
    `scope_type` VARCHAR(16) NOT NULL COMMENT '数据范围类型',
    `value_type` VARCHAR(16) NOT NULL COMMENT '填写值类型',
    `unit` VARCHAR(32) NOT NULL COMMENT '计量单位',
    `required` BOOL NOT NULL COMMENT '是否必填：1是、0否',
    `validation_rule` VARCHAR(255) NOT NULL COMMENT '校验规则',
    `sort_order` INT UNSIGNED NOT NULL COMMENT '项目显示排序号',
    `config_json` LONGTEXT NOT NULL COMMENT '项目扩展配置JSON',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_report_template_item_code` (`template_id`, `task_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='周报模板项目明细表';

CREATE TABLE IF NOT EXISTS `weekly_report` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `submission_id` BIGINT NULL COMMENT '统一主单ID，逻辑关联 report_submission.id',
    `role_code` VARCHAR(64) NOT NULL COMMENT '填写时使用的角色编码',
    `template_code` VARCHAR(64) NOT NULL COMMENT '填写时使用的模板编码（编码已包含版本）',
    `employee_id` BIGINT NOT NULL COMMENT '填报员工ID，逻辑关联 user_account.id',
    `group_id` BIGINT NULL COMMENT '填报时组织分组ID，逻辑关联 organization_group.id',
    `period_type` VARCHAR(16) NOT NULL COMMENT '周期类型，当前为 week',
    `month_key` VARCHAR(7) NOT NULL COMMENT '所属月份，格式 YYYY-MM',
    `period_start` DATE NOT NULL COMMENT '周期开始日期',
    `period_end` DATE NOT NULL COMMENT '周期结束日期',
    `as_of_date` DATE NOT NULL COMMENT '报告统计截至日期',
    `status` VARCHAR(24) NOT NULL COMMENT '报告状态：not_started待开始、in_progress进行中、completed已完成',
    `summary` LONGTEXT NOT NULL COMMENT '本周工作总结',
    `risk_level` VARCHAR(16) NOT NULL COMMENT '风险等级：none无风险、low低风险、medium中风险、high高风险',
    `risk_blocked` BOOL NOT NULL COMMENT '是否存在阻塞风险：1是、0否',
    `risk_reason` LONGTEXT NOT NULL COMMENT '风险或阻塞原因',
    `next_action` LONGTEXT NOT NULL COMMENT '下周重点行动',
    `support_needed` LONGTEXT NOT NULL COMMENT '需要的支持事项',
    `expected_resolve_date` DATE NULL COMMENT '预计风险解决日期',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`),
    KEY `weekly_report_submission_id_01c5f55d` (`submission_id`),
    UNIQUE KEY `uq_weekly_report_employee_role_period` (`employee_id`, `role_code`, `period_start`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='员工周报主表';

CREATE TABLE IF NOT EXISTS `monthly_plan` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `submission_id` BIGINT NULL COMMENT '统一主单ID，逻辑关联 report_submission.id',
    `role_code` VARCHAR(64) NOT NULL COMMENT '月度计划所属角色编码',
    `employee_id` BIGINT NOT NULL COMMENT '填报员工ID，逻辑关联 user_account.id',
    `group_id` BIGINT NULL COMMENT '填报时组织分组ID，逻辑关联 organization_group.id',
    `month_key` VARCHAR(7) NOT NULL COMMENT '计划月度，格式 YYYY-MM',
    `summary` LONGTEXT NOT NULL COMMENT '月度计划概述',
    `template_code` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '模板编码',
    `status` VARCHAR(16) NOT NULL DEFAULT 'draft' COMMENT '草稿/审批中/通过/驳回/删除',
    `revision` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '内容版本',
    `rejection_reason` LONGTEXT NOT NULL COMMENT '最新驳回原因',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`),
    KEY `monthly_plan_submission_id_9061210a` (`submission_id`),
    UNIQUE KEY `uq_monthly_plan_employee_role_month` (`employee_id`, `role_code`, `month_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='员工角色月度共用计划主表';

-- 同一员工、角色、月份共用的月度计划任务明细；与周工作任务独立。
CREATE TABLE IF NOT EXISTS `monthly_plan_task` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `employee_id` BIGINT NOT NULL COMMENT '计划所属员工逻辑ID',
    `role_code` VARCHAR(64) NOT NULL COMMENT '计划所属角色编码',
    `month_key` VARCHAR(7) NOT NULL COMMENT '所属月份YYYY-MM',
    `scope_name` VARCHAR(255) NULL DEFAULT NULL COMMENT '客户或维度，由模板决定显示名称',
    `work_task` LONGTEXT NOT NULL COMMENT '工作任务长文本',
    `work_content` LONGTEXT NOT NULL COMMENT '主要工作内容；可为空文本，接口默认空字符串',
    `output_description` LONGTEXT NOT NULL COMMENT '输出成果，接口默认空字符串',
    `planned_date` DATE NULL COMMENT '计划完成时间',
    `sort_order` INT UNSIGNED NOT NULL COMMENT '列表顺序，从0开始',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_monthly_plan_task_order` (`employee_id`, `role_code`, `month_key`, `sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='月度计划任务明细';

CREATE TABLE IF NOT EXISTS `weekly_report_item` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `report_id` BIGINT NOT NULL COMMENT '周报ID，逻辑关联 weekly_report.id',
    `scope_type` VARCHAR(16) NOT NULL COMMENT '任务数据范围类型',
    `customer_id` BIGINT NULL COMMENT '客户ID，预留逻辑关联客户业务表',
    `customer_name_snapshot` VARCHAR(255) NOT NULL COMMENT '客户名称快照',
    `section_code` VARCHAR(64) NOT NULL COMMENT '模板分区编码快照',
    `task_code` VARCHAR(64) NOT NULL COMMENT '模板任务项编码快照',
    `customer_text_id` BIGINT NULL COMMENT '销售手填客户共享文本逻辑ID，与系统客户无关',
    `dimension_text_id` BIGINT NULL COMMENT '共享维度文本逻辑ID',
    `task_text_id` BIGINT NULL COMMENT '工作任务文本逻辑ID',
    `work_content_text_id` BIGINT NULL COMMENT '工作内容文本逻辑ID',
    `task_name_snapshot` LONGTEXT NOT NULL COMMENT '任务名称快照',
    `guidance_snapshot` VARCHAR(500) NOT NULL COMMENT '填写指引快照',
    `work_content` LONGTEXT NOT NULL COMMENT '主要工作内容',
    `output_description` LONGTEXT NOT NULL COMMENT '本周产出描述',
    `planned_completion_date` DATE NULL COMMENT '计划完成日期',
    `progress_text` LONGTEXT NOT NULL COMMENT '进度说明',
    `progress_percent` DECIMAL(5,2) NULL COMMENT '进度百分比',
    `quality_percent` DECIMAL(5,2) NULL COMMENT '质量百分比',
    `completion_rate` DECIMAL(5,2) NULL COMMENT '综合完成率百分比',
    `on_time_status` VARCHAR(24) NOT NULL COMMENT '任务状态（唯一状态字段）：pending待完成、in_progress进行中、on_time按时完成、late延期完成、overdue逾期未完成、not_applicable不适用、completed已完成',
    `actual_completion_date` DATE NULL COMMENT '实际完成日期',
    `delay_reason` LONGTEXT NOT NULL COMMENT '延期原因',
    `next_action` LONGTEXT NOT NULL COMMENT '该任务下一步行动',
    `expected_completion_date` DATE NULL COMMENT '预计完成日期',
    `owner_id` BIGINT NULL COMMENT '任务负责人ID，逻辑关联 user_account.id',
    `owner_name_snapshot` VARCHAR(128) NOT NULL COMMENT '责任人姓名快照',
    `collaborator_names` VARCHAR(500) NOT NULL COMMENT '协作人姓名，多个以逗号分隔',
    `document_links` LONGTEXT NOT NULL COMMENT '相关文档链接或佐证材料',
    `sort_order` INT UNSIGNED NOT NULL COMMENT '任务项排序号',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='周报任务明细表';

CREATE TABLE IF NOT EXISTS `weekly_report_item_progress_history` (
  `id` bigint NOT NULL COMMENT '雪花算法主键ID',
  `report_id` bigint NOT NULL COMMENT '周报ID，逻辑关联 weekly_report.id',
  `report_item_id` bigint NOT NULL COMMENT '保存快照时的周报任务ID，逻辑关联 weekly_report_item.id',
  `task_code_snapshot` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务编码快照，用于任务覆盖保存后识别同一逻辑任务',
  `progress_percent` decimal(5,2) DEFAULT NULL COMMENT '保存时的进度百分比，范围0—100',
  `quality_percent` decimal(5,2) DEFAULT NULL COMMENT '保存时的质量百分比，范围0—100',
  `completion_rate` decimal(5,2) DEFAULT NULL COMMENT '保存时的综合完成率百分比',
  `on_time_status` varchar(24) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务状态：in_progress进行中、on_time按时完成、late延期完成、overdue已逾期、not_applicable不适用',
  `record_date` date NOT NULL COMMENT '趋势归属日期；超出周报周期时归入周期首日或末日',
  `recorded_by` bigint NOT NULL COMMENT '操作用户ID，逻辑关联 user_account.id',
  `created_at` datetime(6) NOT NULL COMMENT '快照创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_wriph_report_date` (`report_id`,`record_date`),
  KEY `idx_wriph_task_time` (`report_id`,`task_code_snapshot`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='周报任务进度历史快照表';

CREATE TABLE IF NOT EXISTS `weekly_report_metric` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `report_id` BIGINT NOT NULL COMMENT '周报ID，逻辑关联 weekly_report.id',
    `item_id` BIGINT NULL COMMENT '任务明细ID，逻辑关联 weekly_report_item.id',
    `metric_code` VARCHAR(64) NOT NULL COMMENT '指标编码',
    `metric_name_snapshot` VARCHAR(255) NOT NULL COMMENT '指标名称快照',
    `value_type` VARCHAR(16) NOT NULL COMMENT '指标值类型',
    `target_value_decimal` DECIMAL(16,2) NULL COMMENT '指标目标数值',
    `actual_value_decimal` DECIMAL(16,2) NULL COMMENT '指标实际数值',
    `value_text` LONGTEXT NOT NULL COMMENT '指标文本值',
    `unit` VARCHAR(32) NOT NULL COMMENT '指标单位',
    `precision` SMALLINT UNSIGNED NOT NULL COMMENT '指标小数位数',
    `baseline_value_decimal` DECIMAL(16,2) NULL COMMENT '指标基线数值',
    `note` LONGTEXT NOT NULL COMMENT '指标备注',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='周报指标明细表';

CREATE TABLE IF NOT EXISTS `system_attachment` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `attachment_type` VARCHAR(64) NOT NULL COMMENT '业务类型：weekly_report、weekly_report_pending、monthly_plan；不是文件格式',
    `relation_id` BIGINT NOT NULL COMMENT '业务主记录ID，按 attachment_type 解释',
    `relation_sub_id` BIGINT NULL COMMENT '业务子记录ID，预留逻辑关联，不绑定具体模块',
    `storage_key` VARCHAR(512) NOT NULL COMMENT '文件存储键，相对 MEDIA_ROOT 的路径',
    `file_url` LONGTEXT NOT NULL COMMENT '附件访问地址',
    `file_name` VARCHAR(255) NOT NULL COMMENT '用户上传的原始文件名',
    `mime_type` VARCHAR(128) NOT NULL COMMENT '文件 MIME 类型',
    `file_size` BIGINT NOT NULL DEFAULT 0 COMMENT '文件大小，单位字节',
    `description` VARCHAR(500) NOT NULL COMMENT '附件说明',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_system_attachment_relation` (`attachment_type`, `relation_id`, `relation_sub_id`),
    KEY `idx_system_attachment_type` (`attachment_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统通用附件表';

-- ---- AI 网关表（ai_gateway 0001~0004，2026-11-24 新增） ----

CREATE TABLE IF NOT EXISTS `ai_model_config` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `model` VARCHAR(128) NOT NULL COMMENT '对话模型名称，如 gpt-4o、deepseek-chat',
    `vision_model` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '视觉模型名称，空串表示未配置',
    `base_url` VARCHAR(500) NOT NULL DEFAULT '' COMMENT 'OpenAI 兼容接口地址，空串使用内置默认',
    `api_key` LONGTEXT NOT NULL COMMENT 'RSA-OAEP-SHA256 加密后的接口密钥密文',
    `is_enabled` BOOL NOT NULL DEFAULT 1 COMMENT '是否启用：1启用、0停用',
    `last_test_status` VARCHAR(16) NOT NULL DEFAULT '' COMMENT '最近连通性测试状态：ok、fail、空为未测试',
    `last_test_message` VARCHAR(500) NOT NULL DEFAULT '' COMMENT '最近连通性测试结果说明',
    `last_tested_at` DATETIME(6) NULL COMMENT '最近连通性测试时间',
    `updated_by_id` BIGINT NULL COMMENT '最后更新人用户ID，逻辑关联 user_account.id',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI 模型配置表（全局单行配置，对话/视觉模型）';

CREATE TABLE IF NOT EXISTS `ai_chat_attachment` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `uploader_id` BIGINT NOT NULL COMMENT '上传人用户ID，逻辑关联 user_account.id',
    `original_name` VARCHAR(255) NOT NULL COMMENT '用户上传的原始文件名',
    `storage_name` VARCHAR(255) NOT NULL COMMENT '文件存储名，相对 MEDIA_ROOT 的唯一路径',
    `mime_type` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '文件 MIME 类型',
    `file_size` BIGINT NOT NULL DEFAULT 0 COMMENT '文件大小，单位字节',
    `kind` VARCHAR(16) NOT NULL COMMENT '附件类别：image图片、document文档',
    `extracted_text` LONGTEXT NOT NULL COMMENT '文档解析后的纯文本内容，用于对话上下文',
    `extraction_provider` VARCHAR(16) NOT NULL DEFAULT '' COMMENT '文本解析服务商：paddleocr、mineru、baidu，空串表示未解析',
    `extraction_key_id` BIGINT NULL COMMENT '解析所用 OCR 密钥ID，逻辑关联 ai_ocr_key.id',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_ai_chat_attachment_storage_name` (`storage_name`),
    KEY `idx_ai_attachment_owner` (`uploader_id`, `id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI 对话附件表（上传文件与解析文本）';

CREATE TABLE IF NOT EXISTS `ai_ocr_key` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `provider` VARCHAR(16) NOT NULL COMMENT 'OCR 服务商：paddleocr、mineru、baidu',
    `label` VARCHAR(80) NOT NULL DEFAULT '' COMMENT '密钥备注名称',
    `api_key` LONGTEXT NOT NULL COMMENT 'RSA-OAEP-SHA256 加密后的接口密钥密文',
    `is_enabled` BOOL NOT NULL DEFAULT 1 COMMENT '是否启用：1启用、0停用',
    `last_used_at` DATETIME(6) NULL COMMENT '最近使用时间',
    `last_status` VARCHAR(16) NOT NULL DEFAULT '' COMMENT '最近调用状态：ok、fail、空为未使用',
    `last_error` VARCHAR(300) NOT NULL DEFAULT '' COMMENT '最近调用错误信息',
    `use_count` BIGINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '累计调用次数',
    `created_by_id` BIGINT NULL COMMENT '创建人用户ID，逻辑关联 user_account.id',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_ai_ocr_key_enabled` (`provider`, `is_enabled`),
    KEY `idx_ai_ocr_key_is_enabled` (`is_enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='OCR 密钥池表（按服务商轮询可用密钥）';

-- ---- 月度计划任务进度表（weekly_report 0024，2026-11-24 新增） ----

CREATE TABLE IF NOT EXISTS `monthly_plan_task_progress` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `task_id` BIGINT NOT NULL COMMENT '月度计划任务ID，逻辑关联 monthly_plan_task.id；一任务一行',
    `data_json` LONGTEXT NOT NULL COMMENT '进度数据 JSON 快照（随进度卡片结构演进）',
    `revision` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '进度版本号，每次保存自增',
    `updated_by` BIGINT NOT NULL COMMENT '最后更新人用户ID，逻辑关联 user_account.id',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_mptp_task` (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='月度计划任务进度表（当前值，一任务一行）';

CREATE TABLE IF NOT EXISTS `monthly_plan_task_progress_history` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `task_id` BIGINT NOT NULL COMMENT '月度计划任务ID，逻辑关联 monthly_plan_task.id',
    `revision` INT UNSIGNED NOT NULL COMMENT '本次保存后的进度版本号',
    `changed_by` BIGINT NOT NULL COMMENT '操作人用户ID，逻辑关联 user_account.id',
    `before_json` LONGTEXT NOT NULL COMMENT '保存前进度数据 JSON 快照',
    `after_json` LONGTEXT NOT NULL COMMENT '保存后进度数据 JSON 快照',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_mptph_task_revision` (`task_id`, `revision`),
    KEY `idx_mptph_task_time` (`task_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='月度计划任务进度历史表（逐版本快照）';

-- =========================
-- Django 框架表（admin/auth/contenttypes/sessions/migrations）
-- =========================

CREATE TABLE IF NOT EXISTS `django_migrations` (
    `id` BIGINT AUTO_INCREMENT NOT NULL COMMENT 'Django 迁移记录主键',
    `app` VARCHAR(255) NOT NULL COMMENT 'Django 应用标签',
    `name` VARCHAR(255) NOT NULL COMMENT '迁移名称',
    `applied` DATETIME(6) NOT NULL COMMENT '迁移应用时间',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Django 迁移记录表';

CREATE TABLE IF NOT EXISTS `django_content_type` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT '内容类型主键',
    `name` VARCHAR(100) NOT NULL COMMENT '内容类型名称',
    `app_label` VARCHAR(100) NOT NULL COMMENT 'Django 应用标签',
    `model` VARCHAR(100) NOT NULL COMMENT '模型名称',
    PRIMARY KEY (`id`),
    UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`, `model`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Django 内容类型表';

CREATE TABLE IF NOT EXISTS `auth_permission` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT '权限主键',
    `name` VARCHAR(50) NOT NULL COMMENT '权限名称',
    `content_type_id` INT NOT NULL COMMENT '内容类型ID，Django外键',
    `codename` VARCHAR(100) NOT NULL COMMENT '权限编码',
    PRIMARY KEY (`id`),
    UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`, `codename`),
    KEY `auth_permission_content_type_id_2f476e4b` (`content_type_id`),
    CONSTRAINT `fk_auth_permission_content_type`
        FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Django 权限表';

CREATE TABLE IF NOT EXISTS `auth_group` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT '权限组主键',
    `name` VARCHAR(80) NOT NULL COMMENT '权限组名称',
    PRIMARY KEY (`id`),
    UNIQUE KEY `auth_group_name_uniq` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Django 权限组表';

CREATE TABLE IF NOT EXISTS `auth_group_permissions` (
    `id` BIGINT AUTO_INCREMENT NOT NULL COMMENT '权限组关系主键',
    `group_id` INT NOT NULL COMMENT '权限组ID，Django外键',
    `permission_id` INT NOT NULL COMMENT '权限ID，Django外键',
    PRIMARY KEY (`id`),
    UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`, `permission_id`),
    KEY `auth_group_permissions_group_id_b120cbf9` (`group_id`),
    KEY `auth_group_permissions_permission_id_84c5c92e` (`permission_id`),
    CONSTRAINT `fk_group_perm_group`
        FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
    CONSTRAINT `fk_group_perm_permission`
        FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Django 权限组-权限关系表';

CREATE TABLE IF NOT EXISTS `auth_user` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT 'Django 用户主键',
    `password` VARCHAR(128) NOT NULL COMMENT 'Django 密码哈希',
    `last_login` DATETIME(6) NOT NULL COMMENT '最近登录时间',
    `is_superuser` BOOL NOT NULL COMMENT '是否超级管理员：1是、0否',
    `username` VARCHAR(30) NOT NULL COMMENT 'Django 管理后台用户名',
    `first_name` VARCHAR(30) NOT NULL COMMENT '名',
    `last_name` VARCHAR(30) NOT NULL COMMENT '姓',
    `email` VARCHAR(75) NOT NULL COMMENT '邮箱',
    `is_staff` BOOL NOT NULL COMMENT '是否允许进入 Django 管理后台：1是、0否',
    `is_active` BOOL NOT NULL COMMENT '是否启用：1启用、0停用',
    `date_joined` DATETIME(6) NOT NULL COMMENT '加入时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `auth_user_username_uniq` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Django 后台用户表';

CREATE TABLE IF NOT EXISTS `auth_user_groups` (
    `id` BIGINT AUTO_INCREMENT NOT NULL COMMENT '用户-权限组关系主键',
    `user_id` INT NOT NULL COMMENT '用户ID，Django外键',
    `group_id` INT NOT NULL COMMENT '权限组ID，Django外键',
    PRIMARY KEY (`id`),
    UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`, `group_id`),
    KEY `auth_user_groups_user_id_6a12ed8b` (`user_id`),
    KEY `auth_user_groups_group_id_97559544` (`group_id`),
    CONSTRAINT `fk_user_groups_user`
        FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
    CONSTRAINT `fk_user_groups_group`
        FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Django 用户-权限组关系表';

CREATE TABLE IF NOT EXISTS `auth_user_user_permissions` (
    `id` BIGINT AUTO_INCREMENT NOT NULL COMMENT '用户-权限关系主键',
    `user_id` INT NOT NULL COMMENT '用户ID，Django外键',
    `permission_id` INT NOT NULL COMMENT '权限ID，Django外键',
    PRIMARY KEY (`id`),
    UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`, `permission_id`),
    KEY `auth_user_user_permissions_user_id_a95ead1b` (`user_id`),
    KEY `auth_user_user_permissions_permission_id_1fbb5f2c` (`permission_id`),
    CONSTRAINT `fk_user_perm_user`
        FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
    CONSTRAINT `fk_user_perm_permission`
        FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Django 用户-权限关系表';

CREATE TABLE IF NOT EXISTS `django_admin_log` (
    `id` INT AUTO_INCREMENT NOT NULL COMMENT '后台操作日志主键',
    `action_time` DATETIME(6) NOT NULL COMMENT '操作时间',
    `object_id` LONGTEXT NULL COMMENT '被操作对象ID文本',
    `object_repr` VARCHAR(200) NOT NULL COMMENT '被操作对象描述',
    `action_flag` SMALLINT UNSIGNED NOT NULL COMMENT '操作类型标记',
    `change_message` LONGTEXT NOT NULL COMMENT '变更内容',
    `content_type_id` INT NULL COMMENT '内容类型ID，Django外键',
    `user_id` INT NOT NULL COMMENT '操作用户ID，Django外键',
    PRIMARY KEY (`id`),
    KEY `django_admin_log_content_type_id_c4bce8eb` (`content_type_id`),
    KEY `django_admin_log_user_id_c564eba6` (`user_id`),
    CONSTRAINT `fk_admin_log_content_type`
        FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
    CONSTRAINT `fk_admin_log_user`
        FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Django 管理后台操作日志表';

CREATE TABLE IF NOT EXISTS `django_session` (
    `session_key` VARCHAR(40) NOT NULL COMMENT '会话键',
    `session_data` LONGTEXT NOT NULL COMMENT '会话数据',
    `expire_date` DATETIME(6) NOT NULL COMMENT '会话过期时间',
    PRIMARY KEY (`session_key`),
    KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Django 会话表';
-- 周报每日工作任务（日报）：与周报逻辑关联，一个周报每天一条。
CREATE TABLE IF NOT EXISTS `weekly_report_daily_task` (
    `id` BIGINT NOT NULL COMMENT '主键ID，雪花算法生成',
    `report_id` BIGINT NOT NULL COMMENT '周报逻辑ID',
    `work_date` DATE NOT NULL COMMENT '日报日期',
    `work_content` TEXT NOT NULL COMMENT '主要工作内容',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_weekly_report_daily_task_date` (`report_id`, `work_date`),
    KEY `idx_weekly_report_daily_task_report_date` (`report_id`, `work_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='周报每日工作任务（日报）';
-- 月度计划审批管理相关业务表。
-- 直属上级以逻辑 ID 关联，sort_order 从 0 开始，雪花 ID 由应用生成。
CREATE TABLE IF NOT EXISTS `user_manager` (
  `id` BIGINT NOT NULL,
  `user_id` BIGINT NOT NULL,
  `manager_id` BIGINT NOT NULL,
  `sort_order` INT UNSIGNED NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_manager_pair` (`user_id`, `manager_id`),
  UNIQUE KEY `uq_user_manager_order` (`user_id`, `sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='直属上级及顺序';

CREATE TABLE IF NOT EXISTS `business_approval` (
  `id` BIGINT NOT NULL,
  `business_type` VARCHAR(64) NOT NULL,
  `business_id` BIGINT NOT NULL,
  `applicant_id` BIGINT NOT NULL,
  `revision` INT UNSIGNED NOT NULL,
  `status` VARCHAR(16) NOT NULL,
  `current_step` INT UNSIGNED NOT NULL,
  `snapshot_json` LONGTEXT NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  `completed_at` DATETIME(6) NULL,
  PRIMARY KEY (`id`),
  KEY `idx_approval_business` (`business_type`, `business_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通用业务审批单及提交快照';

CREATE TABLE IF NOT EXISTS `business_approval_step` (
  `id` BIGINT NOT NULL,
  `approval_id` BIGINT NOT NULL,
  `approver_id` BIGINT NOT NULL,
  `approver_name` VARCHAR(128) NOT NULL,
  `approver_role_code` VARCHAR(64) NOT NULL,
  `sort_order` INT UNSIGNED NOT NULL,
  `status` VARCHAR(16) NOT NULL,
  `reason` LONGTEXT NOT NULL,
  `acted_at` DATETIME(6) NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_approval_step_order` (`approval_id`, `sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='顺序审批节点及意见';

CREATE TABLE IF NOT EXISTS `monthly_plan_revision` (
  `id` BIGINT NOT NULL,
  `monthly_plan_id` BIGINT NOT NULL,
  `revision` INT UNSIGNED NOT NULL,
  `changed_by` BIGINT NOT NULL,
  `action` VARCHAR(16) NOT NULL,
  `snapshot_json` LONGTEXT NOT NULL,
  `changes_json` LONGTEXT NOT NULL,
  `created_at` DATETIME(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='月度目标和计划变更历史';

-- 月度计划变更子流程；主流程仅保留最后审批通过的生效数据。
CREATE TABLE IF NOT EXISTS `monthly_plan_change` (
 `id` BIGINT NOT NULL,
 `monthly_plan_id` BIGINT NOT NULL,
 `base_revision` INT UNSIGNED NOT NULL,
 `base_snapshot_json` LONGTEXT NOT NULL,
 `proposed_snapshot_json` LONGTEXT NOT NULL,
 `published_snapshot_json` LONGTEXT NOT NULL,
 `effective_revision` INT UNSIGNED NOT NULL,
 `revision` INT UNSIGNED NOT NULL,
 `status` VARCHAR(16) NOT NULL,
 `rejection_reason` LONGTEXT NOT NULL,
 `created_by` BIGINT NOT NULL,
 `created_at` DATETIME(6) NOT NULL,
 `updated_at` DATETIME(6) NOT NULL,
 PRIMARY KEY (`id`),
 KEY `idx_monthly_change_root` (`monthly_plan_id`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='月度计划变更子流程及冻结快照';

-- 通用待办：已读提醒与业务完成状态分别记录；雪花ID，无外键。
CREATE TABLE IF NOT EXISTS `todo_item` (
 `id` BIGINT NOT NULL,
 `recipient_id` BIGINT NOT NULL,
 `role_code` VARCHAR(64) NOT NULL,
 `source` VARCHAR(64) NOT NULL,
 `dedupe_key` VARCHAR(192) NOT NULL,
 `title` VARCHAR(255) NOT NULL,
 `target_json` LONGTEXT NOT NULL,
 `status` VARCHAR(16) NOT NULL,
 `read_at` DATETIME(6) NULL,
 `completed_at` DATETIME(6) NULL,
 `created_at` DATETIME(6) NOT NULL,
 `updated_at` DATETIME(6) NOT NULL,
 PRIMARY KEY (`id`),
 UNIQUE KEY `uq_todo_recipient_key` (`recipient_id`, `role_code`, `dedupe_key`),
 KEY `idx_todo_recipient_status` (`recipient_id`, `role_code`, `status`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通用待办及独立未读提醒';

-- 周报正文共用表；主键由应用雪花算法生成，不使用数据库外键。
CREATE TABLE IF NOT EXISTS weekly_task_text (
 id BIGINT NOT NULL PRIMARY KEY, report_id BIGINT NOT NULL,
 content_type VARCHAR(24) NOT NULL, content LONGTEXT NOT NULL,
 source VARCHAR(16) NOT NULL DEFAULT 'custom', template_text LONGTEXT NOT NULL,
 values_json LONGTEXT NOT NULL, created_at DATETIME(6) NOT NULL, updated_at DATETIME(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 独立月报审批人：不回填直属上级，空配置提交时自动通过。
CREATE TABLE IF NOT EXISTS user_monthly_approver (
  id BIGINT NOT NULL PRIMARY KEY COMMENT '雪花主键',
  user_id BIGINT NOT NULL COMMENT '申请人逻辑ID',
  approver_id BIGINT NOT NULL COMMENT '月报审批人逻辑ID',
  sort_order INT UNSIGNED NOT NULL COMMENT '选择顺序，从0开始',
  CONSTRAINT uq_monthly_approver_pair UNIQUE (user_id, approver_id),
  CONSTRAINT uq_monthly_approver_order UNIQUE (user_id, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


-- 多职位负责客户：默认无客户；仅保存逻辑关联，不建立外键。
CREATE TABLE IF NOT EXISTS `role_customer` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `role_id` BIGINT NOT NULL COMMENT '职位ID，逻辑关联 role.id',
    `customer_id` BIGINT NOT NULL COMMENT '负责客户ID，逻辑关联 system_dictionary.id',
    `sort_order` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '客户选择顺序，从0开始',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_role_customer` (`role_id`, `customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='职位负责客户';

CREATE TABLE IF NOT EXISTS `user_role_customer` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID，逻辑关联 user_account.id',
    `role_id` BIGINT NOT NULL COMMENT '已分配职位ID，逻辑关联 role.id',
    `customer_id` BIGINT NOT NULL COMMENT '用户在该职位下负责的客户ID，逻辑关联 system_dictionary.id',
    `sort_order` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '客户选择顺序，从0开始',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_user_role_customer` (`user_id`, `role_id`, `customer_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户各职位负责客户';

-- 多职位统一填报主单。历史单职位记录分别关联独立 legacy 主单，active_key 留空。
CREATE TABLE IF NOT EXISTS `report_submission` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `merged_into_id` BIGINT NULL COMMENT '合并后的统一主单ID，逻辑关联report_submission.id',
    `kind` VARCHAR(16) NOT NULL COMMENT '单据类型：monthly月度计划、weekly周报',
    `employee_id` BIGINT NOT NULL COMMENT '填报员工ID，逻辑关联 user_account.id',
    `group_id` BIGINT NULL COMMENT '填报组织分组ID，逻辑关联 organization_group.id',
    `month_key` VARCHAR(7) NOT NULL COMMENT '所属月份，格式YYYY-MM',
    `period_start` DATE NULL COMMENT '周报开始日期，月度计划为空',
    `period_end` DATE NULL COMMENT '周报结束日期，月度计划为空',
    `active_key` VARCHAR(128) NULL DEFAULT NULL COMMENT '新单唯一键：类型:员工:周期；历史/删除单为空',
    `status` VARCHAR(24) NOT NULL DEFAULT 'draft' COMMENT 'draft/pending/approved/rejected/not_started/in_progress/completed/deleted',
    `revision` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '整份主单内容版本',
    `legacy` BOOL NOT NULL DEFAULT 0 COMMENT '历史单职位兼容标记，1表示保持原审批流程',
    `submitted_at` DATETIME(6) NULL COMMENT '统一提交时间',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间，历史回填保留原时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '更新时间，历史回填保留原时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_report_submission_active_key` (`active_key`),
    KEY `idx_submission_merged_into` (`merged_into_id`),
    KEY `idx_submission_owner_period` (`employee_id`, `kind`, `month_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='多职位月度计划和周报统一主单';

CREATE TABLE IF NOT EXISTS `report_submission_change` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `submission_id` BIGINT NOT NULL COMMENT '统一主单ID，逻辑关联 report_submission.id',
    `base_revision` INT UNSIGNED NOT NULL COMMENT '申请变更时的生效主单版本',
    `revision` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '变更提案版本',
    `status` VARCHAR(24) NOT NULL DEFAULT 'draft' COMMENT 'draft/pending/approved/rejected/deleted',
    `base_snapshot_json` LONGTEXT NOT NULL COMMENT '原始生效快照，包含全部职位内容',
    `proposed_snapshot_json` LONGTEXT NOT NULL COMMENT '拟变更快照，通过审批前不覆盖生效数据',
    `rejection_reason` LONGTEXT NOT NULL COMMENT '驳回原因，无原因时为空字符串',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间',
    `updated_at` DATETIME(6) NOT NULL COMMENT '最后更新时间',
    PRIMARY KEY (`id`),
    KEY `report_submission_change_submission_id_7dc0721d` (`submission_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='多职位月度计划整单变更及冻结快照';

-- 用户月度计划与周报只读共享（accounts0008）
CREATE TABLE IF NOT EXISTS `user_report_share` (
    `id` BIGINT NOT NULL COMMENT '雪花算法主键ID',
    `owner_id` BIGINT NOT NULL COMMENT '共享数据所有者ID，逻辑关联 user_account.id',
    `recipient_id` BIGINT NOT NULL COMMENT '共享接收人ID，逻辑关联 user_account.id',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_user_report_share` (`owner_id`, `recipient_id`),
    KEY `idx_report_share_recipient` (`recipient_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户月度计划及周报只读共享配置';
