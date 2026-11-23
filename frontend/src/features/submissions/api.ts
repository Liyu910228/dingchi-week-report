/** 月度草稿允许暂存未完成内容，仅提交审批时进行填写校验；提交校验失败返回职位、明细行号、客户/维度/模块、字段及具体原因；模板元数据异常提示系统错误及处理建议，普通填写错误说明修改要求。 */
/** 未提交周报详情临时展开当前职位；保存回传 source_report_id/source_updated_at/source_submission_id 校验来源，读取不落库，已完成记录不展开。 */
/** 历史变更预览展开当前全部填报职位，parts携带source_plan_id/source_revision/source_submission_id冻结来源；保存原样回传，来源更新时400拒绝覆盖。合并仅在审批通过后执行，旧主单ID仍可读取有效主单。 */
/** 月度提交校验所有职位：月度目标非空且至少一条有效计划；失败400并标注职位，整单不提交。 */
import { request } from "@/shared/api/http"
import type {SubmissionKind,SubmissionDetail,SubmissionContext,SubmissionInput,SubmissionChange} from "./types"
/** 多职位统一主单v1新增资源：Bearer/trace，字符串ID、ISO日期；整单revision防覆盖；400参数/状态、401认证、403越权、404不存在、409并发。 */
const base="/v1/report-submissions/"
/** GET配置：本人有效职位、独立模板及负责客户；无客户返回空数组，不授予其他职位权限。 */
export function getSubmissionContext(kind:SubmissionKind,monthKey?:string):Promise<SubmissionContext>{return request({method:"GET",url:`${base}${kind}/context/`,params:{month_key:monthKey}})}
/** GET主单：职位明细保持独立ID，返回可编辑状态与整单审批；授权读取。 */
export function getSubmission(kind:SubmissionKind,id:string):Promise<SubmissionDetail>{return request({method:"GET",url:`${base}${kind}/${id}/`})}
/** POST/PATCH整单保存：parts=[{role_code,template_code,payload}]，同一事务；不切换登录职位。 */
export function saveSubmission(kind:SubmissionKind,input:SubmissionInput,id?:string):Promise<SubmissionDetail>{return request({method:id?"PATCH":"POST",url:`${base}${kind}/${id?id+"/":""}`,data:input})}
/** POST统一提交；月度按有序审批人创建一个流程，空审批配置自动通过；周报逐职位校验后整单完成。 */
export function submitSubmission(kind:SubmissionKind,id:string):Promise<SubmissionDetail>{return request({method:"POST",url:`${base}${kind}/${id}/submit/`})}
/** 其余列表、变更、复制沿用既有列表契约，只把ID改为主单ID；分页按主单计算。 */
export {base as submissionApiBase}

/** GET变更主单，冻结基线与提案均包含全部职位；权限、trace和字符串ID同主单。 */
export function getSubmissionChange(id:string):Promise<SubmissionChange>{return request({method:"GET",url:`${base}changes/${id}/`})}
/** PATCH变更提案，POST提交；revision防覆盖；通过前不修改生效数据，400/403/404/409。 */
export function saveSubmissionChange(id:string,input:SubmissionInput):Promise<SubmissionChange>{return request({method:"PATCH",url:`${base}changes/${id}/`,data:input})}
export function submitSubmissionChange(id:string):Promise<SubmissionChange>{return request({method:"POST",url:`${base}changes/${id}/submit/`})}

/** GET只读准备变更，不创建记录；POST仅在显式保存/提交时创建并保存，base_revision校验原生效版本；失败整单回滚。原因可选最多10000字，沿用字符串ID、Bearer及trace。 */
export function previewSubmissionChange(id:string):Promise<SubmissionChange>{return request({method:"GET",url:`${base}monthly/${id}/change-preview/`})}
export function createSubmissionChange(id:string,input:SubmissionInput,submit=false):Promise<SubmissionChange>{return request({method:"POST",url:`${base}monthly/${id}/changes/`,data:{...input,submit}})}
