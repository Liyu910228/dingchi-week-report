import { request } from "@/shared/api/http"

import type {
  ModelConfiguration,
  ModelConfigurationPayload,
  ModelConfigurationTestResult,
} from "./types"

/**
 * 查询当前 AI 模型配置，供系统管理员查看和编辑。
 * 方法/路径：GET /v1/ai/model-config/（统一客户端拼接 /api）；无请求参数。
 * 响应：ModelConfiguration；API Key 只返回 has_api_key 与掩码，绝不返回原始密钥，时间字段为 ISO 字符串或 null。
 * 权限/安全：需要登录 Bearer 令牌及系统管理员权限；401 未登录，403 非管理员。
 * 错误/追踪：统一错误层处理 400、401、403 及服务端错误并保留 trace_id；请求自动携带 X-Trace-ID。
 * 兼容性：新增响应字段向后兼容，字段改名、改类型或密钥语义变化需升级 API 主版本。
 */
export function getModelConfiguration(): Promise<ModelConfiguration> {
  return request<ModelConfiguration>({ method: "GET", url: "/v1/ai/model-config/" })
}

/**
 * 保存 AI 模型配置。
 * 方法/路径：PUT /v1/ai/model-config/；JSON Body 为 ModelConfigurationPayload。
 * 参数：model、base_url、is_enabled 必填，vision_model 可空；api_key 省略或空字符串表示保留已保存密钥。
 * 响应：保存后的 ModelConfiguration，密钥仍只返回掩码。
 * 权限/安全：仅系统管理员；密钥仅用于本次 HTTPS 请求，不写入 Store 或本地存储。
 * 错误/追踪：400 参数错误、401 未登录、403 非管理员，统一错误层保留 trace_id 并自动携带 X-Trace-ID。
 * 兼容性：新增可选请求/响应字段向后兼容，保留密钥的空值语义不可在旧版本内更改。
 */
export function updateModelConfiguration(
  payload: ModelConfigurationPayload,
): Promise<ModelConfiguration> {
  return request<ModelConfiguration>({
    method: "PUT",
    url: "/v1/ai/model-config/",
    data: payload,
  })
}

/**
 * 使用表单中的模型参数测试 AI 服务连通性，不保存配置。
 * 方法/路径：POST /v1/ai/model-config/test/；JSON Body 为 ModelConfigurationPayload。
 * 参数：与保存接口一致；api_key 省略或为空时使用服务端已保存密钥。
 * 响应：ModelConfigurationTestResult；latency_ms 单位为毫秒，reply 为模型测试回复，success=false 表示业务测试失败。
 * 权限/安全：仅系统管理员；密钥不持久化到前端；401/403 及请求错误由统一错误层抛出并保留 trace_id。
 * 错误/追踪：HTTP 或 envelope 失败统一抛错，请求自动携带 X-Trace-ID，测试接口禁止无确认自动重试。
 * 兼容性：新增响应字段向后兼容，测试成败及密钥回退语义变化需升级 API 主版本。
 */
export function testModelConfiguration(
  payload: ModelConfigurationPayload,
): Promise<ModelConfigurationTestResult> {
  return request<ModelConfigurationTestResult>({
    method: "POST",
    url: "/v1/ai/model-config/test/",
    data: payload,
  })
}
