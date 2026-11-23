/** 统一主单GET列表支持view=shared，仅返回直接共享给当前用户的人员数据；employee_name为可选姓名模糊筛选，最多128字；先授权和筛选再分页。共享详情和附件只读，撤销立即失效，权限不足403。 */
/** 列表、删除、提交及复制改走report-submissions主单资源；按整单分页与事务处理，正文/日报接口仍使用职位明细ID。 */
/** v1多职位兼容扩展：列表聚合账号可见的所有职位；新增通过X-Report-Role指定本人有效填写职位。
 * 本模块统一附加填写上下文，已有记录由后端按所属职位校验；未分配职位403，未认证401；Bearer/trace保持不变。
 */
import { http } from "@/shared/api/http"
import { reportRequest as request } from "@/shared/api/report-context"

import type {
  ReportListFilters,
  ReportListResponse,
  MonthlyPlan,
  ReportPayload,
  ReportTemplate,
  ReportAttachment,
  DailyWorkTask,
  DailyWorkTaskListResponse,
  WeeklyReportDetail,
} from "./types"

/**
 * 获取指定版本周报模板。
 * 方法/路径：GET /v1/weekly-report-templates/{template_code}/；认证：Bearer；幂等：是。
 * 请求参数：路径 template_code，包含版本号的模板编码；响应 data 为模板、任务、指标和按字典配置排序的 fields JSON；
 * 失败：401/400，统一客户端保留 trace_id，页面只展示错误消息。
 */
export function getReportTemplate(templateCode: string): Promise<ReportTemplate> {
  return request<ReportTemplate>({
    method: "GET",
    url: "/v1/weekly-report-templates/" + templateCode + "/",
  })
}

/**
 * 分页查询当前角色可见的周报摘要。
 * 方法/路径：GET /v1/weekly-reports/；认证：Bearer；幂等：是。
 * 请求参数：role_code为可选职位编码（最多64字符，空值全部），只与原有权限取交集；筛选后分页与统计total。
 * page/page_size 为正整数（默认 1/10）；period_start、period_end 为
 * YYYY-MM-DD 周期范围上下限，month_key 为 YYYY-MM 所属月度；team 角色可传 employee_scope=self/team；团队和全员角色可传
 * group_id 字符串筛选分组；employee_id 字符串筛选指定人员（服务端仍按当前角色可见范围校验）。响应 data.items 为周报数组，并返回 page、page_size、total、
 * total_pages；ID 为字符串，失败 400/401/403/404，统一客户端携带 trace_id。
 */
export function listReports(filters: ReportListFilters = {}): Promise<ReportListResponse> {
  return request<ReportListResponse>({
    method: "GET",
    url: "/v1/report-submissions/weekly/",
    params: filters,
  })
}

/**
 * 获取当前用户当前角色指定月度的共用计划。
 * 方法/路径：GET /v1/monthly-plans/{month_key}/；认证：Bearer；幂等：是。
 * 路径参数 month_key 为 YYYY-MM；响应 data 为月度目标文本，未填写时为 null；
 * 失败：400/401/403，统一客户端携带 trace_id。
 */
export function getMonthlyPlan(monthKey: string): Promise<MonthlyPlan | null> {
  return request<MonthlyPlan | null>({
    method: "GET",
    url: "/v1/monthly-plans/" + monthKey + "/",
  })
}

/**
 * 保存当前用户当前角色指定月度的计划文本。
 * 方法/路径：PUT /v1/monthly-plans/{month_key}/；认证：Bearer；幂等：是。
 * 请求体：summary 月度目标文本；响应 data 为保存后的月度目标；失败：400/401/403。
 */
export function saveMonthlyPlan(monthKey: string, summary: string): Promise<MonthlyPlan> {
  return request<MonthlyPlan>({
    method: "PUT",
    url: "/v1/monthly-plans/" + monthKey + "/",
    data: { summary },
  })
}

/**
 * 创建当前用户当前角色的周报。
 * 方法/路径：POST /v1/weekly-reports/；认证：Bearer；幂等：否。
 * 请求体：period_start/period_end、动态 items、summary；统计日期由服务端按当前日期处理；
 * monthly_plan_tasks 可选，最多 200 条，每项 work_task 必填且最多 2000 字符，
 * scope_name 为客户/维度（最多255字符，显示该字段的模板必填，职能可为空），顺序按数组；
 * 随周报事务替换本人当前角色当月共用计划，省略保留；
 * 月度目标和计划不能为空，空数组会返回 400 INVALID_REQUEST。
 * 支持创建历史、当前或未来周期，周期不能重复。响应 data 为完整周报详情；失败 400/401/409，
 * 统一客户端携带 trace_id，页面不得依赖后端实现细节。
 */
// 所有模板允许不完整草稿；业务必填项和模板占位值统一在提交时校验。
/**
 * 任务正文兼容契约：task_name_snapshot/work_content 继续返回字符串。
 * 新增 task_text_id/work_content_text_id（字符串逻辑ID）、task_group_key/work_content_group_key（草稿分组）。
 * 共享同一引用/分组的行必须传一致正文。任务来源 task_source=custom/template；
 * task_template 保留模板原文，task_values 是每个问号对应的字符串数组。交付、招聘、销售和职能的模板来源任务仅可改占位值。
 * 销售手填客户支持 customer_text_id/group_key/source/template/values；文本ID为字符串，source为custom/template，
 * values为每项最多256字的占位值数组；与系统客户ID无关，省略时按独立自定义文本处理；新增字段兼容旧数据。
 * 招聘维度新增可选 dimension_text_id/group_key/source/template/values，与任务的同名后缀字段语义相同。
 * 维度ID为字符串、source=custom/template、values为每项最多256字的字符串数组；省略时兼容旧数据。
 * 缺省来源按 custom 处理；引用跨周报、类型不匹配或共享文本冲突返回400，仍统一携带 trace_id。
 */
export function createReport(payload: ReportPayload): Promise<WeeklyReportDetail> {
  return request<WeeklyReportDetail>({ method: "POST", url: "/v1/weekly-reports/", data: payload })
}

/**
 * 更新本人当前周报。
 * 方法/路径：PATCH /v1/weekly-reports/{id}/；认证：Bearer；幂等：否。
 * 请求体字段同创建；所有模板草稿允许必填项为空，提交前统一检查。
 * 周报周期不可修改且仅本人未完成周报可编辑；
 * 响应 data 为更新后的详情，月度计划明细按员工、角色、月份共用；
 * 失败 400/401/403/404/409，统一客户端携带 trace_id。
 */
export function updateReport(reportId: string, payload: ReportPayload): Promise<WeeklyReportDetail> {
  return request<WeeklyReportDetail>({
    method: "PATCH",
    url: "/v1/weekly-reports/" + reportId + "/",
    data: payload,
  })
}

/**
 * 查询周报详情。
 * 方法/路径：GET /v1/weekly-reports/{id}/；认证：Bearer；幂等：是。
 * 当前角色必须对该员工可见；响应 data 返回 report/template/monthly_plan/items/metrics/attachments/daily_tasks；
 * template 按 report.template_code 返回周报创建时绑定的完整版本模板；
 * monthly_plan_tasks 为当前月份共用计划列表，ID 为字符串，work_task 为工作任务，按 sort_order 排序；
 * 失败 401/403/404，ID 和日期字段遵守统一 JSON 契约。
 */
export function getReportDetail(reportId: string): Promise<WeeklyReportDetail> {
  return request<WeeklyReportDetail>({
    method: "GET",
    url: "/v1/weekly-reports/" + reportId + "/",
  })
}

/**
 * 查询指定周报的每日工作任务。
 * 方法/路径：GET /v1/weekly-reports/{id}/daily-tasks/；认证：Bearer；幂等：是。
 * 无分页参数，响应 data.items 按日期升序返回日报；日期为 YYYY-MM-DD，逻辑 ID 为字符串；
 * 当前角色必须对周报可见，失败 401/403/404，统一客户端携带 trace_id。
 */
export function getDailyTasks(reportId: string): Promise<DailyWorkTaskListResponse> {
  return request<DailyWorkTaskListResponse>({
    method: "GET",
    url: "/v1/weekly-reports/" + reportId + "/daily-tasks/",
  })
}

/**
 * 新增周报中的每日工作任务。
 * 方法/路径：POST /v1/weekly-reports/{id}/daily-tasks/；认证：Bearer；幂等：否。
 * 请求体：work_date（YYYY-MM-DD）和 work_content；日期必须在周报周期内且每天只能一条；
 * 仅本人进行中状态周报可新增，成功返回日报记录，失败 400/401/403/404/409。
 */
export function createDailyTask(
  reportId: string,
  payload: Pick<DailyWorkTask, "work_date" | "work_content">,
): Promise<DailyWorkTask> {
  return request<DailyWorkTask>({
    method: "POST",
    url: "/v1/weekly-reports/" + reportId + "/daily-tasks/",
    data: payload,
  })
}

/**
 * 修改周报中的每日工作任务。
 * 方法/路径：PATCH /v1/weekly-reports/{id}/daily-tasks/{daily_task_id}/；认证：Bearer；幂等：否。
 * 请求体字段同新增；仅本人进行中状态周报可修改，成功返回日报记录，失败 400/401/403/404/409。
 */
export function updateDailyTask(
  reportId: string,
  dailyTaskId: string,
  payload: Pick<DailyWorkTask, "work_date" | "work_content">,
): Promise<DailyWorkTask> {
  return request<DailyWorkTask>({
    method: "PATCH",
    url: "/v1/weekly-reports/" + reportId + "/daily-tasks/" + dailyTaskId + "/",
    data: payload,
  })
}

/**
 * 删除周报中的每日工作任务。
 * 方法/路径：DELETE /v1/weekly-reports/{id}/daily-tasks/{daily_task_id}/；认证：Bearer；幂等：否。
 * 无请求体；仅本人进行中状态周报可删除，成功返回 {id, deleted:true}，失败 401/403/404。
 */
export function deleteDailyTask(
  reportId: string,
  dailyTaskId: string,
): Promise<{ id: string; deleted: true }> {
  return request<{ id: string; deleted: true }>({
    method: "DELETE",
    url: "/v1/weekly-reports/" + reportId + "/daily-tasks/" + dailyTaskId + "/",
  })
}

/**
 * 删除本人当前周报。
 * 方法/路径：DELETE /v1/weekly-reports/{id}/；认证：Bearer；幂等：否。
 * 无请求体；仅本人且未完成的周报可删除，响应 data 为 { id: string, deleted: true }；
 * 失败 400/401/403/404，统一客户端携带 trace_id。
 */
export function deleteReport(reportId: string): Promise<{ id: string; deleted: true }> {
  return request<{ id: string; deleted: true }>({
    method: "DELETE",
    url: "/v1/report-submissions/weekly/" + reportId + "/",
  })
}

/**
 * 手动提交本人当前角色的周报。
 * 方法/路径：POST /v1/weekly-reports/{id}/submit/；认证：Bearer；幂等：否。
 * 仅进行中状态的本人周报可以提交，提交后周报及其任务、日报、附件只读。
 */
// 交付专员任务缺少输出成果或计划完成日期时返回 400，周报保持未提交。
export function submitReport(
  reportId: string,
): Promise<{ id: string; status: "completed"; submitted: true }> {
  return request<{ id: string; status: "completed"; submitted: true }>({
    method: "POST",
    url: "/v1/report-submissions/weekly/" + reportId + "/submit/",
  })
}

/**
 * 上传尚未绑定工作任务的附件。
 * 方法/路径：POST /v1/attachments/；认证：Bearer；幂等：否。
 * 请求体：multipart/form-data，file 必填，description 可选。
 * 成功响应返回附件 ID；保存周报工作任务时再通过附件 ID 建立业务关联。
 */
export function uploadPendingReportAttachment(
  file: File,
  description = "",
): Promise<ReportAttachment> {
  const data = new FormData()
  data.append("file", file)
  if (description) data.append("description", description)
  return request<ReportAttachment>({
    method: "POST",
    url: "/v1/attachments/",
    data,
  })
}

/**
 * 物理删除周报附件。
 * 方法/路径：DELETE /v1/attachments/{attachment_id}/；认证：Bearer；幂等：否。
 * 仅周报本人且周报未提交时允许操作；成功后附件表记录和磁盘文件均被删除。
 */
export function deleteReportAttachment(
  attachmentId: string,
): Promise<{ id: string; deleted: true }> {
  return request<{ id: string; deleted: true }>({
    method: "DELETE",
    url: "/v1/attachments/" + attachmentId + "/",
  })
}

/**
 * 鉴权下载附件。
 * 方法/路径：GET /v1/attachments/{attachment_id}/download/；认证：Bearer；幂等：是。
 * 当前职位必须对附件所属周报/月度计划具有查看或审批权限（待绑定附件仅上传本人）；响应为二进制文件流，不暴露存储路径。
 */
export async function downloadReportAttachment(
  attachmentId: string,
  fileName: string,
): Promise<void> {
  const response = await http.get<Blob>(
    "/v1/attachments/" + attachmentId + "/download/",
    { responseType: "blob" },
  )
  const objectUrl = URL.createObjectURL(response.data)
  const anchor = document.createElement("a")
  anchor.href = objectUrl
  anchor.download = fileName || "附件"
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(objectUrl)
}


/**
 * 将本人当前职位已完成周报复制到紧邻下一周期。
 * POST /v1/weekly-reports/{reportId}/copy/；Bearer 认证；无请求体。
 * 响应 ID 为字符串，日期 YYYY-MM-DD，新周报及明细、共享正文使用全新 ID；不生成日报。
 * 400 状态或月度审批校验失败，403 无权限，404 不存在，409 目标周期已有周报；
 * 错误经统一客户端保留 trace_id；新增接口兼容旧契约，重复调用不重复创建。
 */
export function copyReport(reportId: string): Promise<{
  id: string
  status: string
  period_start: string
  period_end: string
}> {
  return request({ method: "POST", url: `/v1/report-submissions/weekly/${reportId}/copy/` })
}


/** POST恢复误提交周报：仅系统管理员，整份已完成周报恢复进行中，填写内容保留。
 * 参数为字符串主单ID；返回id、status、revision、restored。400状态不符/403越权/404不存在；
 * Bearer及X-Trace-ID由统一HTTP客户端附加，不授予普通用户恢复权限。
 */
export function reopenReport(reportId: string): Promise<{id:string;status:"in_progress";revision:number;restored:true}> {
  return request({method:"POST",url:`/v1/report-submissions/weekly/${reportId}/reopen/`})
}
