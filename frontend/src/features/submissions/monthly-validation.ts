import type { SubmissionPart } from "./types"

/** 提交前检查全部职位，草稿保存不触发此校验。 */
export function monthlySubmissionErrors(parts: SubmissionPart[]) {
  return parts.flatMap(part => {
    const missing: string[] = []
    if (!part.payload.summary?.trim()) missing.push("月度目标填写内容校验不通过：请填写月度目标")
    if ((part.payload.summary?.length || 0)>10000) missing.push("月度目标填写内容校验不通过：不能超过10000字符，请缩短后提交")
    if (!part.payload.tasks?.length) missing.push("月度计划填写内容校验不通过：请至少填写一条月度计划")
    return missing.length ? [{roleCode: part.role_code, message: `${part.role_name || part.role_code}：${missing.join("；")}。`}] : []
  })
}
