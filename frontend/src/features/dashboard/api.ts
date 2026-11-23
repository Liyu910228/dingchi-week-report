import { request } from "@/shared/api/http"

import type { DashboardNextWeek, DashboardSummary } from "./types"

/**
 * 获取周报驾驶舱：GET /v1/dashboard/summary/（统一客户端拼接 /api）。
 * periodStart 可选且必须是周一；服务端按激活角色和指定周期返回个人/团队/全量维度的 KPI、趋势、分布和任务。
 * member_reports 为当前周期按成员去重、更新时间降序的摘要，数量不超过可见成员数；status=completed 才算已提交。
 * my_tasks/team_tasks 继续返回原明细；my_work_tasks/team_work_tasks 按 report_id、客户、task_text_id 聚合，缺少文本引用的独立行不按名称合并。
 * 聚合字段 progress_percent/completion_rate 为明细均值，detail_count/completed_detail_count/detail_completion_rate 表示明细总数、完成数与占比；全部完成才计整项完成。
 * member_stats/group_stats/KPI/trend 按逻辑任务统计；output_task_count/output_count/output_distribution 按全部成果明细统计，不依赖200条展示上限。
 * team_output_items 为最多200条成果原始明细，保留每条实际进度、质量、综合完成率和日期。
 * 错误：AUTHENTICATION_FAILED、INTERNAL_ERROR；http 层保留 X-Trace-ID；响应字段只增不删。
 */
export function getDashboardSummary(periodStart?: string): Promise<DashboardSummary> {
  return request<DashboardSummary>({
    method: "GET",
    url: "/v1/dashboard/summary/",
    params: periodStart ? { period_start: periodStart } : undefined,
  })
}

/**
 * 获取所选周期紧邻下一周的数据：GET /v1/dashboard/next-week/。
 * 服务端严格查询 periodStart + 7 天所在周期；空周返回空数组，不会跳到更远的有数据周期。
 * my_plans/team_tasks 保留明细，my_work_plans/team_work_tasks 为按共享工作任务引用分组后的计划。
 */
export function getDashboardNextWeek(periodStart?: string): Promise<DashboardNextWeek> {
  return request<DashboardNextWeek>({
    method: "GET",
    url: "/v1/dashboard/next-week/",
    params: periodStart ? { period_start: periodStart } : undefined,
  })
}
