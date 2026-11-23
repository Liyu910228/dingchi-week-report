import { request } from "@/shared/api/http"

import type { Customer, CustomerMutationPayload, DictionaryItem } from "./types"

/**
 * 查询启用的静态字典项，供角色配置等页面使用。
 * 方法/路径：GET /v1/dictionaries/{dictType}/（统一客户端拼接 /api）；无请求体。
 * 路径参数：dictType 使用小写下划线编码，例如 role_scope、report_template。
 * 响应：data.items 按 sort_order 排序，包含 dict_code、dict_name、dict_value 等展示和校验字段。
 * 失败：401 表示未登录，400 表示字典类型编码非法；请求自动携带 Bearer Token 与 X-Trace-ID。
 */
export function listDictionaryItems(dictType: string): Promise<{ items: DictionaryItem[] }> {
  return request<{ items: DictionaryItem[] }>({
    method: "GET",
    url: `/v1/dictionaries/${encodeURIComponent(dictType)}/`,
  })
}

/**
 * 查询客户配置列表，供系统管理员维护客户编号与名称。
 * 方法/路径：GET /v1/dictionaries/customers/（统一客户端拼接 /api）；无请求体。
 * 权限：仅系统管理员；其他角色返回 403。
 * 响应：data.items 按 sort_order 升序，包含 id、dict_code（客户编号）、dict_name（客户名称）、
 * status、sort_order、description。
 * 失败：401 未登录，403 非系统管理员；请求自动携带 Bearer Token 与 X-Trace-ID。
 */
export function listCustomers(): Promise<{ items: Customer[] }> {
  return request<{ items: Customer[] }>({ method: "GET", url: "/v1/dictionaries/customers/" })
}

/**
 * 新增客户配置。
 * 方法/路径：POST /v1/dictionaries/customers/new/；权限：仅系统管理员。
 * 请求体：dict_code 必填，仅英文字母和数字，1–64 字符；dict_name 必填，1–128 字符；
 * sort_order、description 可选。
 * 响应：201 客户对象；失败：400 INVALID_REQUEST、409 CUSTOMER_CONFLICT（编号重复）。
 */
export function createCustomer(payload: CustomerMutationPayload): Promise<Customer> {
  return request<Customer>({
    method: "POST",
    url: "/v1/dictionaries/customers/new/",
    data: payload,
  })
}

/**
 * 修改客户配置。
 * 方法/路径：PATCH /v1/dictionaries/customers/{id}/；路径 id 为 Snowflake 字符串。
 * 请求体：dict_name（1–128 字符）、sort_order、status、description 任选；dict_code 创建后不可修改。
 * 响应：更新后的客户对象；不存在返回 404 CUSTOMER_NOT_FOUND。
 */
export function updateCustomer(
  id: string,
  payload: Partial<CustomerMutationPayload>,
): Promise<Customer> {
  return request<Customer>({
    method: "PATCH",
    url: `/v1/dictionaries/customers/${id}/`,
    data: payload,
  })
}

/**
 * 软删除客户配置，历史周报引用保留。
 * 方法/路径：DELETE /v1/dictionaries/customers/{id}/；权限：仅系统管理员。
 * 响应：id 与 deleted=true；不存在返回 404 CUSTOMER_NOT_FOUND。
 */
export function deleteCustomer(id: string): Promise<{ id: string; deleted: true }> {
  return request<{ id: string; deleted: true }>({
    method: "DELETE",
    url: `/v1/dictionaries/customers/${id}/`,
  })
}
