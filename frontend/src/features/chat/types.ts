export type ChatRole = "system" | "user" | "assistant"

export interface ChatAttachment {
  id: string
  name: string
  mime_type: string
  size: number
  kind: "image" | "document"
}

export interface ChatMessage {
  role: ChatRole
  content: string
  attachment_ids?: string[]
}

export interface ChatResult {
  content: string
  model: string
  request_id: string | null
  usage: {
    input_tokens: number | null
    output_tokens: number | null
    total_tokens: number | null
  }
}

export interface ChatEntry {
  id: string
  role: ChatRole
  content: string
  attachments?: ChatAttachment[]
}
