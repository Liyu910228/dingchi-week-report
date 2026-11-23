"""Built-in role templates used before the database seed is applied.

Template items are persisted by ``docs/数据库脚本/02_初始化DML.sql`` and task-list
columns are optionally overridden by the versioned template field dictionaries.  Keeping a
small fallback makes the local UI useful while a developer is preparing MySQL.
"""

from __future__ import annotations

from typing import Any

from .template_definitions.human_resources import (
    human_resources_definition,
    human_resources_fields,
)


def _task_fields() -> list[dict[str, Any]]:
    """Return the built-in task-list columns in the Excel-defined order.

    The order is part of the template contract rather than an implementation
    detail of the Vue table.  A dictionary override can replace these values
    without changing the report tables or the task editor form.
    """
    labels = [
        ("customer_name", "客户"),
        ("task_name", "工作任务"),
        ("work_content", "主要工作内容"),
        ("output_description", "输出成果"),
        ("planned_completion_date", "计划完成时间"),
        ("progress_text", "工作进展（截至月日）"),
        ("progress_percent", "完成进度（百分比）"),
        ("delay_reason", "进度缓慢原因说明"),
        ("on_time_status", "是否在计划时间内完成"),
        ("actual_completion_date", "实际完成时间"),
        ("owner_name", "责任人"),
        ("collaborator_names", "协作人"),
        ("document_links", "相关文档链接或佐证材料"),
    ]
    default_visible = {
        "customer_name",
        "task_name",
        "output_description",
        "planned_completion_date",
        "progress_percent",
        "on_time_status",
    }
    return [
        {
            "field_code": code,
            "label": label,
            "sort_order": index,
            "default_visible": code in default_visible,
        }
        for index, (code, label) in enumerate(labels, start=1)
    ]


def _functional_group_task_fields() -> list[dict[str, Any]]:
    """Return the delivery-compatible columns without the customer column.

    职能组记录的是跨部门职能事项，不以客户作为任务主维度；其余字段
    仍与交付专员模板保持同一 Excel 顺序，方便复用列表和任务编辑能力。
    """
    labels = [
        ("task_name", "工作任务"),
        ("work_content", "主要工作内容"),
        ("output_description", "输出成果"),
        ("planned_completion_date", "计划完成时间"),
        ("progress_text", "工作进展（截至月日）"),
        ("progress_percent", "完成进度（百分比）"),
        ("delay_reason", "进度缓慢原因说明"),
        ("on_time_status", "是否在计划时间内完成"),
        ("actual_completion_date", "实际完成时间"),
        ("owner_name", "责任人"),
        ("collaborator_names", "协作人"),
        ("document_links", "相关文档链接或佐证材料"),
    ]
    return [
        {
            "field_code": code,
            "label": label,
            "sort_order": index,
            "default_visible": True,
        }
        for index, (code, label) in enumerate(labels, start=1)
    ]


def _delivery_assistant_task_fields() -> list[dict[str, Any]]:
    """Return the delivery-assistant Excel columns in their original order.

    The assistant workbook has two additional quality columns compared with
    the delivery-specialist workbook. completion_rate is calculated by
    the service from progress and quality and is therefore read-only in
    the task editor, while the dictionary still controls whether it is shown
    in the list.
    """
    labels = [
        ("customer_name", "客户"),
        ("task_name", "工作任务"),
        ("work_content", "主要工作内容"),
        ("output_description", "输出成果"),
        ("planned_completion_date", "计划完成时间"),
        ("progress_text", "工作进展（截至月日）"),
        ("progress_percent", "完成进度（百分比）"),
        ("quality_percent", "完成质量（百分比）"),
        ("completion_rate", "月度工作完成率（完成进度*50%+完成质量*50%）"),
        ("delay_reason", "进度缓慢原因说明"),
        ("on_time_status", "是否在计划时间内完成"),
        ("actual_completion_date", "实际完成时间"),
        ("owner_name", "责任人"),
        ("collaborator_names", "协作人"),
        ("document_links", "相关文档链接或佐证材料"),
    ]
    default_visible = {
        "customer_name",
        "task_name",
        "output_description",
        "planned_completion_date",
        "progress_percent",
        "quality_percent",
        "completion_rate",
        "on_time_status",
    }
    return [
        {
            "field_code": code,
            "label": label,
            "sort_order": index,
            "default_visible": code in default_visible,
        }
        for index, (code, label) in enumerate(labels, start=1)
    ]


def _recruitment_task_fields() -> list[dict[str, Any]]:
    """Return the shared recruitment workbook columns in their source order.

    招聘专员和招聘经理使用同一份《招聘周报模板》；模板以“维度”代替
    交付类模板中的“客户”，其余任务字段沿用 Excel 的 16 列定义。
    """
    labels = [
        ("dimension", "维度"),
        ("task_name", "工作任务"),
        ("work_content", "主要工作内容"),
        ("output_description", "输出成果"),
        ("planned_completion_date", "计划完成时间"),
        ("progress_text", "工作进展（截至月日）"),
        ("progress_percent", "完成进度（百分比）"),
        ("quality_percent", "完成质量（百分比）"),
        ("completion_rate", "月度工作完成率（完成进度*50%+完成质量*50%）"),
        ("delay_reason", "进度缓慢原因说明"),
        ("on_time_status", "是否在计划时间内完成"),
        ("actual_completion_date", "实际完成时间"),
        ("owner_name", "责任人"),
        ("collaborator_names", "协作人"),
        ("document_links", "相关文档链接或佐证材料"),
    ]
    return [
        {
            "field_code": code,
            "label": label,
            "sort_order": index,
            "default_visible": True,
        }
        for index, (code, label) in enumerate(labels, start=1)
    ]


def _ito_sales_task_fields() -> list[dict[str, Any]]:
    """Return the ITO sales workbook columns in their source order.

    ITO sales uses the same task data contract as the delivery workbooks, but
    the source Excel calls ``work_content`` "主要工作指引".  Keeping this
    label in the versioned template definition means the list and detail views
    can render the original business vocabulary without role-based branches.
    """
    labels = [
        ("customer_name", "客户"),
        ("task_name", "工作任务"),
        ("work_content", "主要工作指引"),
        ("output_description", "输出成果"),
        ("planned_completion_date", "计划完成时间"),
        ("progress_text", "工作进展（截至月日）"),
        ("progress_percent", "完成进度（百分比）"),
        ("quality_percent", "完成质量（百分比）"),
        ("completion_rate", "月度工作完成率（完成进度*50%+完成质量*50%）"),
        ("delay_reason", "进度缓慢原因说明"),
        ("on_time_status", "是否在计划时间内完成"),
        ("actual_completion_date", "实际完成时间"),
        ("owner_name", "责任人"),
        ("collaborator_names", "协作人"),
        ("document_links", "相关文档链接或佐证材料"),
    ]
    return [
        {
            "field_code": code,
            "label": label,
            "sort_order": index,
            "default_visible": True,
        }
        for index, (code, label) in enumerate(labels, start=1)
    ]


# Field order/visibility can be overridden by system_dictionary rows named
# ``weekly_report_fields_{template_code}``.  The template code includes the
# version (for example ``delivery_assistant_v1``), so a new version receives
# an independent field dictionary and never changes an older report layout.
def _innovation_sales_task_fields() -> list[dict[str, Any]]:
    """Return the innovation-sales workbook columns in their source order."""
    labels = [
        ("customer_name", "客户"),
        ("task_name", "工作任务"),
        ("work_content", "主要工作内容"),
        ("output_description", "输出成果"),
        ("planned_completion_date", "计划完成时间"),
        ("progress_text", "工作进展（截至月日）"),
        ("progress_percent", "完成进度（百分比）"),
        ("quality_percent", "完成质量（百分比）"),
        ("completion_rate", "月度工作完成率（完成进度*50%+完成质量*50%）"),
        ("delay_reason", "进度缓慢原因说明"),
        ("on_time_status", "是否在计划时间内完成"),
        ("actual_completion_date", "实际完成时间"),
        ("owner_name", "责任人"),
        ("collaborator_names", "协作人"),
        ("document_links", "相关文档链接或佐证材料"),
    ]
    return [
        {
            "field_code": code,
            "label": label,
            "sort_order": index,
            "default_visible": True,
        }
        for index, (code, label) in enumerate(labels, start=1)
    ]


TEMPLATE_TASK_FIELDS: dict[str, list[dict[str, Any]]] = {
    "human_resources_v1": human_resources_fields(),
    "delivery_specialist_v1": _task_fields(),
    "functional_group_v1": _functional_group_task_fields(),
    "delivery_assistant_v1": _delivery_assistant_task_fields(),
    "recruitment_v1": _recruitment_task_fields(),
    "ito_sales_v1": _ito_sales_task_fields(),
    "innovation_sales_v1": _innovation_sales_task_fields(),
}


def _role_for_template_code(template_code: str) -> str:
    """Resolve a built-in template code to its owning reference role."""
    for candidate_role, source in ROLE_TEMPLATES.items():
        if source["template_code"] == template_code:
            return candidate_role
    raise ValueError(f"周报模板不存在：{template_code}")


def get_default_task_fields(template_code: str) -> list[dict[str, Any]]:
    """Return a copy of a template's built-in task-list column definition."""
    # A custom database template can use the common Excel-compatible columns
    # until its own dictionary rows are configured.  This is only a field
    # shape fallback; template content is still looked up by its exact code.
    fields = TEMPLATE_TASK_FIELDS.get(template_code) or _task_fields()
    return [dict(item) for item in fields]


def _task(
    section_code: str, section_name: str, code: str, label: str, guidance: str
) -> dict[str, Any]:
    return {
        "item_type": "task",
        "section_code": section_code,
        "section_name": section_name,
        "task_code": code,
        "label": label,
        "guidance": guidance,
        "scope_type": "customer" if section_code in {"customer", "delivery"} else "overall",
        "value_type": "text",
        "unit": "",
        "required": False,
    }


def _metric(
    section_code: str, section_name: str, code: str, label: str, unit: str = "个"
) -> dict[str, Any]:
    return {
        "item_type": "metric",
        "section_code": section_code,
        "section_name": section_name,
        "task_code": code,
        "label": label,
        "guidance": "填写本周目标与实际值，单位清晰可追溯。",
        "scope_type": "overall",
        "value_type": "number",
        "unit": unit,
        "required": False,
    }


ROLE_TEMPLATES: dict[str, dict[str, Any]] = {
    "recruitment_specialist": {
        "role_name": "招聘专员",
        "template_code": "recruitment_v1",
        "template_name": "招聘周报",
        "description": (
            "招聘专员和招聘经理共用的招聘周报模板，按月计划、需求管理和其他工作记录招聘进展。"
        ),
        "sections": [
            ("overall", "总体目标"),
            ("demand", "需求管理"),
            ("other", "其他"),
        ],
        "metrics": [
            ("overall", "总体目标", "resume_recommendations", "简历推荐", "份"),
            ("overall", "总体目标", "interviews", "到面人数", "人"),
            ("overall", "总体目标", "onboarded", "有效入职", "人"),
            ("demand", "需求管理", "demand_response_rate", "需求响应率", "%"),
        ],
        "tasks": [
            (
                "overall",
                "总体目标",
                "recruitment_goal",
                "招聘目标推进",
                "记录月度招聘目标、客户入职目标和招聘成果。",
            ),
            (
                "demand",
                "需求管理",
                "demand_response",
                "识别重点需求与响应",
                "记录重点客户需求确认、岗位优先级和招聘协同目标。",
            ),
            ("other", "其他", "other_work", "其他工作", "填写不属于以上模块的招聘工作。"),
        ],
    },
    "delivery_specialist": {
        "role_name": "交付专员",
        "template_code": "delivery_specialist_v1",
        "template_name": "交付专员周总结计划",
        "description": "围绕客户交付、招聘转化、成本和回款填写周报。",
        "sections": [
            ("overall", "总体目标"),
            ("customer", "客户需求和招聘转化"),
            ("risk", "风险控制"),
            ("other", "其他工作"),
        ],
        "metrics": [
            ("overall", "总体目标", "net_headcount", "净增人数", "人"),
            ("customer", "客户需求和招聘转化", "new_demands", "新增需求数", "个"),
            ("customer", "客户需求和招聘转化", "incremental_onboarded", "增量入职人数", "人"),
            ("overall", "总体目标", "collection_amount", "回款金额", "万元"),
            ("risk", "风险控制", "high_risk_items", "高风险事项", "个"),
        ],
        "tasks": [
            (
                "customer",
                "客户需求和招聘转化",
                "customer_progress",
                "重点客户交付进展",
                "按客户记录需求、入职与交付成果。",
            ),
            (
                "risk",
                "风险控制",
                "risk_resolution",
                "延期/风险项处理",
                "必须填写原因、下一步和预计完成日期。",
            ),
            ("other", "其他工作", "other_work", "其他工作", "填写不属于以上模块的交付物。"),
        ],
    },
    "functional_group": {
        "role_name": "职能组",
        "template_code": "functional_group_v1",
        "template_name": "职能组周报",
        "description": "参考交付周报模板记录职能事项、工作成果、进度和协作信息。",
        "sections": [
            ("overall", "总体目标"),
            ("work", "重点工作"),
            ("risk", "风险控制"),
            ("other", "其他工作"),
        ],
        "metrics": [
            ("overall", "总体目标", "net_headcount", "净增人数", "人"),
            ("work", "重点工作", "new_demands", "新增事项数", "项"),
            ("work", "重点工作", "incremental_onboarded", "完成事项数", "项"),
            ("overall", "总体目标", "collection_amount", "预算/回款金额", "万元"),
            ("risk", "风险控制", "high_risk_items", "高风险事项", "项"),
        ],
        "tasks": [
            (
                "work",
                "重点工作",
                "functional_work_progress",
                "重点工作进展",
                "记录职能工作事项、主要工作内容、输出成果和协作安排。",
            ),
            (
                "risk",
                "风险控制",
                "risk_resolution",
                "延期/风险项处理",
                "必须填写原因、下一步和预计完成日期。",
            ),
            ("other", "其他工作", "other_work", "其他工作", "填写不属于以上模块的职能工作。"),
        ],
    },
    "delivery_assistant": {
        "role_name": "交付助理",
        "template_code": "delivery_assistant_v1",
        "template_name": "交付助理周总结计划",
        "description": "围绕人员流失、交付风险、成本和客户维护填写周报。",
        "sections": [
            ("overall", "总体目标"),
            ("customer", "客户交付与人员管控"),
            ("risk", "风险与成本控制"),
            ("other", "其他工作"),
        ],
        "metrics": [
            ("overall", "总体目标", "attrition_count", "流失控制人数", "人"),
            ("overall", "总体目标", "replacement_count", "离职替补人数", "人"),
            ("customer", "客户交付与人员管控", "total_headcount", "当月总人数", "人"),
            ("risk", "风险与成本控制", "high_risk_items", "中高风险人数", "人"),
            ("other", "其他工作", "customer_visits", "客情拜访数", "次"),
        ],
        "tasks": [
            (
                "customer",
                "客户交付与人员管控",
                "headcount_and_attrition",
                "人员流失与替补目标",
                "记录客户人员构成、流失控制、离职替补和空岗人日目标。",
            ),
            (
                "risk",
                "风险与成本控制",
                "release_and_risk_control",
                "释放、风险与成本控制",
                "记录客户释放、风险人员、假期、成本和报价调薪管控措施。",
            ),
            (
                "customer",
                "客户交付与人员管控",
                "customer_relationship",
                "客情与员工沟通",
                "记录客情维护、员工沟通和客户拜访安排。",
            ),
            (
                "other",
                "其他工作",
                "other_work_arrangement",
                "其他工作安排",
                "记录外派员工入职培训、礼品发放、体检安排等事项。",
            ),
        ],
    },
    "delivery_manager": {
        "role_name": "交付经理",
        "template_code": "delivery_manager_v1",
        "template_name": "交付经理周总结计划",
        "description": "汇总交付团队、客户经营、回款和风险。",
        "sections": [("team", "交付团队"), ("customer", "客户经营"), ("risk", "风险与支持")],
        "metrics": [
            ("team", "交付团队", "team_completion_rate", "团队完成率", "%"),
            ("customer", "客户经营", "collection_amount", "回款金额", "万元"),
            ("risk", "风险与支持", "high_risk_items", "高风险事项", "个"),
        ],
        "tasks": [
            ("team", "交付团队", "team_review", "交付团队复盘", "汇总交付专员与交付助理工作。"),
            (
                "customer",
                "客户经营",
                "customer_review",
                "重点客户经营",
                "记录合同、续签、回款及客情。",
            ),
            (
                "risk",
                "风险与支持",
                "risk_resolution",
                "风险闭环",
                "记录阻塞、责任人与预计解除日期。",
            ),
        ],
    },
    "president": {
        "role_name": "总裁",
        "template_code": "president_v1",
        "template_name": "总裁经营周报",
        "description": "从全局视角填写经营重点、关键决策和组织风险。",
        "sections": [("business", "经营概览"), ("decision", "关键决策"), ("risk", "经营风险")],
        "metrics": [
            ("business", "经营概览", "overall_completion_rate", "整体完成率", "%"),
            ("business", "经营概览", "collection_amount", "本周回款", "万元"),
            ("risk", "经营风险", "high_risk_items", "高风险事项", "个"),
        ],
        "tasks": [
            (
                "business",
                "经营概览",
                "business_review",
                "经营重点复盘",
                "填写跨部门关键进展与结果。",
            ),
            (
                "decision",
                "关键决策",
                "decision_items",
                "关键决策事项",
                "填写需要管理层拍板的事项。",
            ),
            (
                "risk",
                "经营风险",
                "risk_resolution",
                "经营风险处置",
                "填写风险影响、支持和预计解除日期。",
            ),
        ],
    },
    "system_admin": {
        "role_name": "系统管理员",
        "template_code": "system_admin_v1",
        "template_name": "系统运营周报",
        "description": "填写系统运行、数据质量和运营支持事项。",
        "sections": [("operation", "系统运营"), ("data", "数据质量"), ("other", "其他工作")],
        "metrics": [
            ("operation", "系统运营", "service_availability", "服务可用率", "%"),
            ("data", "数据质量", "report_completion_rate", "周报提交率", "%"),
            ("data", "数据质量", "data_issues", "数据问题数", "个"),
        ],
        "tasks": [
            (
                "operation",
                "系统运营",
                "service_operation",
                "系统运行维护",
                "记录发布、告警和问题闭环。",
            ),
            ("data", "数据质量", "data_quality", "数据质量巡检", "记录用户、角色和周报数据检查。"),
            ("other", "其他工作", "other_work", "其他工作", "填写运维支持类专项。"),
        ],
    },
    "ito_sales": {
        "role_name": "ITO销售",
        "template_code": "ito_sales_v1",
        "template_name": "ITO销售周报",
        "description": "按照 ITO 销售模板记录月度目标、市场开拓、客户关系和签约收入。",
        "sections": [
            ("overall", "月度目标"),
            ("market", "市场开拓"),
            ("relationship", "客户关系管理"),
            ("contract", "新签合同销售收入"),
            ("other", "其他"),
        ],
        "metrics": [
            ("overall", "月度目标", "target_signings", "目标客户签约数", "家"),
            ("overall", "月度目标", "new_opportunities", "新增机会", "家"),
            ("overall", "月度目标", "win_rate", "中标率", "%"),
            ("overall", "月度目标", "signed_contracts", "合同签订数", "家"),
            ("overall", "月度目标", "new_contract_revenue", "新签合同销售收入", "万元"),
            ("overall", "月度目标", "new_contract_demands", "新签合同需求数", "个"),
            ("overall", "月度目标", "effective_onboarded", "有效入职人数", "个"),
        ],
        "tasks": [
            (
                "overall", "月度目标", "monthly_goal", "月度目标",
                "记录目标客户签约、新增机会、中标率、合同收入和客户关系目标。",
            ),
            (
                "market", "市场开拓", "market_development", "市场开拓",
                "记录老客户和新客户机会盘点、机会策略及招投标协同。",
            ),
            (
                "relationship", "客户关系管理", "customer_relationship", "客户关系管理",
                "按目标客户记录教练、内线、决策链、客户画像和拜访计划。",
            ),
            (
                "contract", "新签合同销售收入", "new_contract_revenue_task", "新签合同销售收入",
                "记录新增需求、客户关系维护和合同收入推进。",
            ),
            ("other", "其他", "other_work", "其他", "填写其他销售专项工作。"),
        ],
    },
    "innovation_sales": {
        "role_name": "创新业务销售",
        "template_code": "innovation_sales_v1",
        "template_name": "创新业务销售周总结计划",
        "description": "围绕创新业务机会、方案、签约和回款填写周报。",
        "sections": [("customer", "客户与机会"), ("business", "方案与签约"), ("other", "其他工作")],
        "metrics": [
            ("customer", "客户与机会", "new_opportunities", "新增业务机会", "个"),
            ("business", "方案与签约", "solution_submissions", "方案提交数", "个"),
            ("business", "方案与签约", "signed_amount", "签约金额", "万元"),
        ],
        "tasks": [
            (
                "customer", "客户与机会", "innovation_opportunity", "创新业务机会推进",
                "记录机会识别、客户沟通和需求澄清。",
            ),
            (
                "business", "方案与签约", "solution_and_signing", "方案与签约推进",
                "记录方案提交、商务谈判和签约节点。",
            ),
            ("other", "其他工作", "other_work", "其他工作", "填写其他创新业务专项工作。"),
        ],
    },
}

# 两个招聘角色共用同一份、同一版本的模板定义；角色本身仍保留，供权限
# 范围和页面标题使用。任何模板字段或任务调整只需维护 recruitment_v1 一份。
ROLE_TEMPLATES["recruitment_manager"] = {
    **ROLE_TEMPLATES["recruitment_specialist"],
    "role_name": "招聘经理",
}


ROLE_TEMPLATES["innovation_sales"].update(
    {
        "template_name": "创新业务销售周报",
        "description": "围绕目标客户签约、市场开拓、客户关系和应收款管理填写周报。",
        "sections": [
            ("market", "市场开拓"),
            ("relationship", "客户关系管理"),
            ("receivable", "应收款管理"),
        ],
        "metrics": [
            ("market", "市场开拓", "target_signings", "目标客户签约数", "家"),
            ("market", "市场开拓", "new_opportunities", "新增机会点", "家"),
            ("market", "市场开拓", "new_opportunity_amount", "新增机会额", "万元"),
            ("market", "市场开拓", "win_rate", "中标率", "%"),
            ("market", "市场开拓", "existing_project_revenue", "存量项目营业收入", "万元"),
            ("market", "市场开拓", "new_project_revenue", "新增项目营业收入", "万元"),
            ("relationship", "客户关系管理", "customer_coaches", "客户教练", "名"),
            ("relationship", "客户关系管理", "customer_insiders", "客户内线", "名"),
            ("receivable", "应收款管理", "receivable_recovery_rate", "应收款回款率", "%"),
        ],
        "tasks": [
            (
                "market",
                "市场开拓",
                "market_development",
                "市场开拓",
                "记录目标客户签约、新增机会、营业收入、存量项目管理、新项目机会管理和招投标管理。",
            ),
            (
                "relationship",
                "客户关系管理",
                "customer_relationship",
                "客户关系管理",
                "记录新客户中高层关系推进、客户分级管理、拜访和客户画像。",
            ),
            (
                "receivable",
                "应收款管理",
                "receivables_management",
                "应收款管理",
                "记录应收款回款率和超期应收款处理策略。",
            ),
        ],
    }
)


ROLE_TEMPLATES["human_resources"] = human_resources_definition()


def get_default_template(template_code: str, role_code: str | None = None) -> dict[str, Any]:
    """Build the exact built-in template identified by its versioned code.

    ``role_code`` is only an optional display context for custom roles that
    reuse an existing template.  It never participates in template lookup.
    """
    source_role_code = _role_for_template_code(template_code)
    source = ROLE_TEMPLATES[source_role_code]
    display_role_code = role_code or source_role_code
    sections = [
        {"section_code": code, "section_name": name, "tasks": []}
        for code, name in source["sections"]
    ]
    section_map = {item["section_code"]: item for item in sections}
    items: list[dict[str, Any]] = []
    for index, (section_code, section_name, code, label, guidance, *_rest) in enumerate(
        source["tasks"]
    ):
        item = _task(section_code, section_name, code, label, guidance)
        item["sort_order"] = index
        item["required"] = code != "other_work"
        section_map[section_code]["tasks"].append(item)
        items.append(item)
    metrics: list[dict[str, Any]] = []
    for index, (section_code, section_name, code, label, unit) in enumerate(source["metrics"]):
        item = _metric(section_code, section_name, code, label, unit)
        item["sort_order"] = index
        metrics.append(item)
    return {
        "role_code": display_role_code,
        "role_name": ROLE_TEMPLATES.get(display_role_code, source)["role_name"],
        "template_code": source["template_code"],
        "template_name": source["template_name"],
        "description": source["description"],
        "sections": sections,
        "tasks": items,
        "metrics": metrics,
        "fields": get_default_task_fields(template_code),
    }
