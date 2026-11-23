export const CHAT_ATTACHMENT_ACCEPT =
  "image/png,image/jpeg,image/webp,image/gif,.pdf,.docx,.xlsx,.txt,.md,.csv,.json"
export const MAX_CHAT_ATTACHMENTS = 4
export const MAX_CHAT_ATTACHMENT_SIZE = 10 * 1024 * 1024
export const DEFAULT_ATTACHMENT_PROMPT =
  "请阅读附件内容，提取工作事项、进展、风险和后续计划，并整理成周报草稿。"
export const WEEKLY_REPORT_ATTACHMENT_PROMPT =
  "请根据附件内容，提取本周完成事项、进展、风险和后续计划，并整理成周报草稿。"
export const MONTHLY_PLAN_ATTACHMENT_PROMPT =
  "请根据附件内容，提取本月工作进展、下月目标、重点任务、风险和所需支持，并整理成月度计划草稿。"

const supportedMimeTypes = new Set([
  "image/png",
  "image/jpeg",
  "image/webp",
  "image/gif",
  "application/pdf",
  "text/plain",
  "text/markdown",
  "text/csv",
  "application/json",
])
const supportedExtensions = /\.(png|jpe?g|webp|gif|pdf|docx|xlsx|txt|md|csv|json)$/i
const imageExtensions = /\.(png|jpe?g|webp|gif)$/i

export function isSupportedChatAttachment(file: File): boolean {
  if (file.type.startsWith("image/")) return supportedMimeTypes.has(file.type)
  return supportedMimeTypes.has(file.type) || supportedExtensions.test(file.name)
}

export function isImageChatAttachment(file: File): boolean {
  return ["image/png", "image/jpeg", "image/webp", "image/gif"].includes(file.type) ||
    (!file.type && imageExtensions.test(file.name))
}

export function formatAttachmentSize(size: number): string {
  if (!Number.isFinite(size) || size < 0) return "未知大小"
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}
