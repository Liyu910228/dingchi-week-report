import { defineStore } from "pinia"
import { computed, ref, watch } from "vue"

import { DEFAULT_ATTACHMENT_PROMPT } from "@/features/chat/attachments"
import { useAuthStore } from "@/features/auth/store"
import { getErrorMessage } from "@/shared/api/errors"
import { createId } from "@/utils/id"

import { createChatCompletion, uploadChatAttachment } from "./api"
import type { ChatAttachment, ChatEntry, ChatMessage } from "./types"

/** 聊天记录按登录用户隔离持久化，key 形如 dingchi.chat.<userId>。 */
const CHAT_KEY_PREFIX = "dingchi.chat."
const ANONYMOUS_KEY = "anonymous"

function loadEntries(userId: string): ChatEntry[] {
  try {
    const raw = localStorage.getItem(CHAT_KEY_PREFIX + userId)
    if (!raw) return []
    const parsed = JSON.parse(raw) as ChatEntry[]
    return Array.isArray(parsed) ? parsed : []
  } catch {
    localStorage.removeItem(CHAT_KEY_PREFIX + userId)
    return []
  }
}

export const useChatStore = defineStore("chat", () => {
  const auth = useAuthStore()

  const messages = ref<ChatEntry[]>([])
  const isSending = ref(false)
  const error = ref("")
  const activeModel = ref("")

  const hasMessages = computed(() => messages.value.length > 0)
  const userId = computed(() => (auth.user?.id != null ? String(auth.user.id) : ANONYMOUS_KEY))

  // 账号切换 / 登出时自动切换到对应账号的会话记录，实现隔离。
  watch(
    userId,
    (id, oldId) => {
      if (id === oldId) return
      messages.value = loadEntries(id)
      activeModel.value = ""
      error.value = ""
    },
    { immediate: true },
  )

  function persist() {
    try {
      localStorage.setItem(CHAT_KEY_PREFIX + userId.value, JSON.stringify(messages.value))
    } catch {
      // 存储失败（如配额超限）时静默降级为仅内存会话。
    }
  }

  async function send(content: string, files: File[] = []) {
    const prompt = content.trim() || (files.length ? DEFAULT_ATTACHMENT_PROMPT : "")
    if (!prompt || isSending.value) return

    isSending.value = true
    error.value = ""

    try {
      const attachments: ChatAttachment[] = []
      for (const file of files) attachments.push(await uploadChatAttachment(file))
      messages.value.push({ id: createId(), role: "user", content: prompt, attachments })
      const history: ChatMessage[] = messages.value.map(
        ({ role, content: text, attachments: items }) => ({
          role,
          content: text,
          ...(items?.length ? { attachment_ids: items.map((item) => item.id) } : {}),
        }),
      )
      const result = await createChatCompletion(history)
      activeModel.value = result.model
      messages.value.push({
        id: createId(),
        role: "assistant",
        content: result.content,
      })
      persist()
    } catch (requestError) {
      error.value = getErrorMessage(requestError)
    } finally {
      isSending.value = false
    }
  }

  function clear() {
    localStorage.removeItem(CHAT_KEY_PREFIX + userId.value)
    messages.value = []
    activeModel.value = ""
    error.value = ""
  }

  return { messages, isSending, error, activeModel, hasMessages, send, clear }
})
