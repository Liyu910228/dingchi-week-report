import { ref } from "vue"
import { defineStore } from "pinia"

export type NoticeType = "reminder" | "warning"

export interface NoticeItem {
  id: number
  type: NoticeType
  message: string
}

let nextNoticeId = 1

export const useNoticeStore = defineStore("notice", () => {
  const notices = ref<NoticeItem[]>([])

  function remove(id: number) {
    notices.value = notices.value.filter((notice) => notice.id !== id)
  }

  function show(type: NoticeType, message: string) {
    const normalizedMessage = message.trim()
    if (!normalizedMessage) return
    const id = nextNoticeId++
    notices.value.push({ id, type, message: normalizedMessage })
    if (type === "reminder") window.setTimeout(() => remove(id), 2000)
  }

  function reminder(message: string) {
    show("reminder", message)
  }

  function warning(message: string) {
    show("warning", message)
  }

  return { notices, remove, reminder, warning }
})
