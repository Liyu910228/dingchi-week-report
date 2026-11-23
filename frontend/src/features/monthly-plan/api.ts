/** 历史申请标题优先使用snapshot.parts或snapshot.role_name/code；旧单缺少职位字段时由后端按来源计划补充role_name/code，不使用用户当前职位列表。 */
/** 月度列表及变更兼容新增role_summaries数组，按职位提供role_code/role_name/summary；保留原summary文本，旧单可省略。 */
/** 统一主单GET列表兼容扩展view=shared、employee_name可选姓名模糊筛选（最多128字）；仅直接共享给我的人员，全部职位聚合，先过滤后分页；共享不授予编辑或审批权限，取消共享后旧链接失效。 */
/** 月度任务附件兼容扩展：attachments为可选数组（每项id为字符串、description最多500字，每行最多100个）；
 * 上传复用/v1/attachments/，保存时校验归属并绑定月度计划；响应补齐文件名、类型、大小和附件列表。
 * 下载沿用鉴权接口，支持计划可见人员及审批人；移除仅影响当前版本，保留历史快照；非法400/越权403，Bearer及trace不变。 */
/** v1多职位兼容扩展：列表/审批聚合全部可见职位，返回role_code/role_name。
 * 新增、context、gate通过X-Report-Role指定本人填写职位；已有记录使用记录职位，审批按本人当前节点。
 * 字符串ID、分页、Bearer及trace保持兼容；非法职位403，无模板400；不切换登录会话。
 */
import { reportRequest as request } from "@/shared/api/report-context"
import type {SubmissionDetail,SubmissionChange} from "@/features/submissions/types"
import type { ChangeDetail, PlanContext, PlanDetail, PlanFilters, PlanGate, PlanInput, PlanList } from "./types"

const root="/v1/report-submissions/monthly/"
const changes="/v1/report-submissions/changes/"
const approvals="/v1/report-submissions/approvals/"
const base = "/v1/monthly-plan-management/"
/** 查询本人当前角色的模板及按顺序审批人；GET context/，无参数；Bearer/X-Trace-ID；返回告警和可创建状态，401认证失败。 */
export function getPlanContext(): Promise<PlanContext> { return request<PlanContext>({ method: "GET", url: base + "context/" }).then(context => ({...context, warning: context.warning.replaceAll("角色", "职位")})) }
/** 月度计划筛选分页：GET；view=mine/members/approvals，月份、状态、职位role_code（可选字符串最多64字符，空值全部）、人员/分组ID、pending_only及分页；审批视图按每次提交分页，返回本人分配的审批记录及has_approval_tasks；400/401/403。 */
export function listMonthlyPlans(params: PlanFilters): Promise<PlanList> { return request({ method: "GET", url: root, params }) }
/** 读取指定计划、任务、审批快照及变更历史；GET {id}/，ID为字符串；可见范围及审批人鉴权；401/403/404，统一trace。 */
export function getManagedPlan(id: string): Promise<PlanDetail> { return request({ method: "GET", url: base + id + "/" }) }
/** 月度明细v1兼容扩展：进展progress_text、delay_reason、owner_name、collaborator_names、document_links为可选文本，最多10000字符；
 * progress_percent/quality_percent为0~100数值或null（按0），completion_rate由服务端按两者平均值四舍五入计算；
 * on_time_status为pending/in_progress/on_time/late/overdue/completed/not_applicable，默认in_progress；
 * actual_completion_date为YYYY-MM-DD或空文本；owner_id为数字字符串或null；缺省保留旧客户端兼容性，响应及审批/变更快照返回同名字段。
 * Bearer权限、统一success包络和X-Trace-ID沿用原契约；字段非法返回400 INVALID_REQUEST，禁止记录完整任务内容。
 * 保存本人计划：POST新增、PATCH修改；月份、目标、任务必填；工作任务为长文本；可带customer_source/customer_template/customer_values（销售手填客户，非系统客户）和dimension_source/dimension_template/dimension_values和task_source/task_template/task_values（来源、模板原文、每项最多256字的占位值，旧数据默认custom）；任务可带scope_group_key/task_group_key（当前计划内的客户或维度/任务分组标识，非空字符串、最多128字符；旧数据省略时各行独立）；任务可带work_content/output_description（各最多10000字符，默认空文本）、planned_date（YYYY-MM-DD或null）、content_group_key（工作内容分组标识，最多128字符）；修改携带revision防覆盖；审批中禁止；400/401/403，返回完整详情。 */
export function saveManagedPlan(input: PlanInput, id?: string): Promise<PlanDetail> { return request({ method: id ? "PATCH" : "POST", url: base + (id ? id + "/" : ""), data: input }) }
/** 提交审批：POST {id}/submit/，无请求体；按有序上级创建新审批单及快照；不可重复，驳回需先修改；400/403，返回详情。 */
export function submitManagedPlan(id: string): Promise<SubmissionDetail> { return request({ method: "POST", url: root + id + "/submit/" }) }
/** 软删除本人计划并留历史：DELETE {id}/；审批中禁止；403/404/400；返回字符串id和deleted，trace统一。 */
export function deleteManagedPlan(id: string): Promise<{id: string; deleted: true}> { return request({ method: "DELETE", url: root + id + "/" }) }
/** 按序审批：POST {id}/decide/；action=approve/reject，驳回reason必填最多2000字符；只有当前审批人可操作；400/403/404，返回详情。 */
export function decideManagedPlan(id: string, action: "approve" | "reject", reason: string, approvalId?: string): Promise<SubmissionDetail> { return request({ method: "POST", url: approvals + approvalId + "/decide/", data: {action, reason, approval_id: approvalId} }) }
/** 检查本人当前角色指定月份已审批计划：GET gate/{YYYY-MM}/；返回approved/message和只读内容；用于周报加载及周期切换，400/401，trace统一。 */
export function getMonthlyPlanGate(month: string): Promise<PlanGate> { return request({ method: "GET", url: base + "gate/" + encodeURIComponent(month) + "/" }) }

export interface MonthlyTaskProgressUpdate {task_id:string;revision:number;values:Partial<import("@/features/weekly-report/monthly-plan/types").MonthlyPlanTask>;updated_at?:string;updated_by?:string;updated_by_name?:string}
/** 独立保存右侧执行进度；revision为该任务进度版本，不是计划版本。 */
export function updateMonthlyTaskProgress(taskId:string,input:Partial<import("@/features/weekly-report/monthly-plan/types").MonthlyPlanTask> & {revision:number}):Promise<MonthlyTaskProgressUpdate>{return request({method:"PATCH",url:"/v1/monthly-plan-tasks/"+taskId+"/progress/",data:input})}

/** 显式创建已通过计划的变更草稿（兼容接口，不用于打开变更页面）：POST {id}/changes/，无请求体；锁定基准版本，有未完成申请返回400；Bearer、trace，返回独立申请及原始/拟变更快照，不修改生效数据。 */
export function createPlanChange(id:string):Promise<SubmissionChange> { return request({method:"POST",url:root+id+"/changes/"}) }
/** GET changes/{id}/：查看获授权的变更快照、不可变原始快照和审批记录；字符串ID；401/403/404，统一trace。 */
export function getPlanChange(id:string):Promise<ChangeDetail> { return request({method:"GET",url:base+"changes/"+id+"/"}) }
/** PATCH changes/{id}/：保存目标/tasks/revision，月份不可变；审批中不可编辑；原始快照不可写；400/403/404，返回ChangeDetail。 */
export function savePlanChange(id:string,input:PlanInput):Promise<ChangeDetail> { return request({method:"PATCH",url:base+"changes/"+id+"/",data:input}) }
/** POST changes/{id}/submit/：逐级审批变更，未改内容或基准版本过期返回400；主流程保持生效。 */
export function submitPlanChange(id:string):Promise<SubmissionChange> { return request({method:"POST",url:changes+id+"/submit/"}) }
/** POST changes/{id}/decide/：action、reason、approval_id，驳回原因必填；最终通过原子发布到主流程，401/403/400；返回ChangeDetail。 */
export function decidePlanChange(id:string,action:"approve"|"reject",reason:string,approvalId:string):Promise<SubmissionDetail> { return request({method:"POST",url:approvals+approvalId+"/decide/",data:{action,reason,approval_id:approvalId}}) }
/** DELETE changes/{id}/：删除本人草稿或驳回的变更申请并保留审批历史；主流程不变，400/403/404。 */
export function deletePlanChange(id:string):Promise<{id:string;deleted:true}> { return request({method:"DELETE",url:changes+id+"/"}) }

/** GET approvals/{id}/：本人分配审批单的冻结快照及变更基线，不受列表筛选分页影响；Bearer/trace，400/401/403；返回ApprovalRecord，v1新增。 */
export function getAssignedApproval(id:string):Promise<import("./types").ApprovalRecord>{return request({method:"GET",url:approvals+id+"/"})}

/** POST {id}/copy/，无请求体；仅本人当前职位审批通过主计划；以最新生效内容创建下月独立草稿，排除未通过变更；返回PlanDetail，所有ID为字符串；400未通过或下月已存在、401/403/404/409，统一Bearer和X-Trace-ID，v1新增。 */
export function copyManagedPlan(id: string): Promise<SubmissionDetail> { return request({ method: "POST", url: root + id + "/copy/" }) }
