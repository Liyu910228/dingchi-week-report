import { request } from "@/shared/api/http"

import type { ChatAttachment, ChatMessage, ChatResult } from "./types"

/**
 * 调用后端大模型生成聊天回复。
 * 用途：根据按顺序提供的 system/user/assistant 消息生成一条文本结果，支持引用历史上传附件继续追问。
 * 请求：POST /v1/ai/chat/（统一客户端拼接 /api）；Body 为 messages 非空数组，最多 50 条，
 *   每条 content 非空且不超过 20,000 字符，总长度不超过 100,000；用户消息可携带 attachment_ids 字符串数组，
 *   ID 来自附件上传接口，历史消息中的附件 ID 原样保留；当前接口非幂等，禁止无幂等键自动重试。
 * 认证/权限：使用登录后的 Bearer 令牌，未登录时返回 401；附件仅可引用当前用户有权访问的记录。
 * 响应：返回 ChatResult；content/model 为字符串，request_id 和 usage 字段可空，ID 按 string 处理。
 * 错误：AUTHENTICATION_FAILED、INVALID_JSON、INVALID_REQUEST、AI_NOT_CONFIGURED、AI_PROVIDER_ERROR、INTERNAL_ERROR；
 *   统一错误层保留 trace_id，页面只展示安全提示，请求自动携带 X-Trace-ID。
 * 兼容性：新增可选 attachment_ids 与响应字段向后兼容，字段改名/改类型或消息语义变化需升级 API 主版本。
 */
export function createChatCompletion(messages: ChatMessage[]): Promise<ChatResult> {
  return request<ChatResult>({
    method: "POST",
    url: "/v1/ai/chat/",
    data: { messages },
    // 云端 OCR 需要提交任务并轮询，聊天请求不能使用默认的 30 秒超时。
    timeout: 240000,
  })
}

/**
 * 上传一个供 AI 对话使用的图片或文档附件。
 * 方法/路径：POST /v1/ai/attachments/；Body 为 multipart/form-data，文件字段名 file，每次仅上传一个文件。
 * 参数：支持 PNG、JPEG、WebP、GIF、PDF、DOCX、XLSX、TXT、MD、CSV、JSON；前端选择区最多保留 4 个文件。
 * 响应：ChatAttachment；id 为字符串，name 为原始文件名，mime_type 为媒体类型，size 单位为字节，kind 为 image/document。
 * 认证/安全：使用登录 Bearer 令牌；请求自动删除 JSON Content-Type 以生成 multipart boundary，并携带 X-Trace-ID。
 * 错误/追踪：400 文件缺失、类型或大小不合法，401 未登录，413 文件过大；统一错误层保留 trace_id。
 * 兼容性：新增响应字段向后兼容，字段改名、改类型或附件访问权限语义变化需升级 API 主版本。
 */
export function uploadChatAttachment(file: File): Promise<ChatAttachment> {
  const data = new FormData()
  data.append("file", file)
  return request<ChatAttachment>({
    method: "POST",
    url: "/v1/ai/attachments/",
    data,
  })
}
