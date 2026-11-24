import { request } from "@/shared/api/http";
import type { MonthPage, MonthDetail } from "./types";
/** 月度周报只读查询：GET v1接口；默认members按账号最大有效数据范围查询（本人/团队/全员），mine仅本人；月份/职位/姓名筛选、分页；人员+月详情。
 * Bearer与X-Trace-ID由公共客户端附加；ID为字符串；400参数/401登录/403权限/404无数据。
 * 只聚合所属月度，保留历史职位与模板；响应字段只增不改。 */
export function listMonths(params: Record<string, string | number>) { return request<MonthPage>({ url: "/v1/monthly-weekly-reports/", method: "GET", params }); }
export function getMonth(employee: string, month: string) { return request<MonthDetail>({ url: `/v1/monthly-weekly-reports/${employee}/${month}/`, method: "GET" }); }
