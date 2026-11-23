import type { AxiosRequestConfig } from "axios"
import { request } from "./http"

let roleCode = ""
export function setReportRole(value: string) { roleCode = value }
export function getReportRole() { return roleCode }
/** 报告v1接口使用本人填写职位；Bearer/trace仍由http统一处理。越权职位403，旧接口参数兼容。 */
export function reportRequest<T>(config: AxiosRequestConfig): Promise<T> {
  return request<T>({ ...config, headers: { ...config.headers, ...(roleCode ? { "X-Report-Role": roleCode } : {}) } })
}
