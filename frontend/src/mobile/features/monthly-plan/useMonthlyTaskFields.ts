import { mobileStorage as localStorage } from "@/mobile/shared/storage"
import { computed, ref, watch } from "vue"
import { listUserOptions } from "@/mobile/features/directory/api"
import type { DirectoryUserOption } from "@/mobile/features/directory/types"
import { getReportTemplate } from "@/mobile/features/weekly-report/api"
import { type TaskFieldDefinition } from "@/mobile/features/weekly-report/task-draft"
import { monthlyTaskFieldDefinitions, type MonthlyTaskFieldDefinition } from "./task-field-definitions"

/** 与对应周任务共用字段定义；月度计划使用独立的展示偏好。 */
export function useMonthlyTaskFields(templateCode: () => string | undefined) {
  const users = ref<DirectoryUserOption[]>([])
  const fields = ref<MonthlyTaskFieldDefinition[]>([])
  const columnsOpen = ref(false)
  const selected = ref<string[]>([])
  const error = ref("")
  const storageKey = computed(() => `monthly-plan:visible-columns:${templateCode()}:v1`)
  const availableFields = computed(() => fields.value.filter((field): field is TaskFieldDefinition => !["customer_name", "dimension", "task_name"].includes(field.code)).sort((a, b) => a.sort_order - b.sort_order))
  const selectedFields = computed(() => availableFields.value.filter(field => selected.value.includes(field.code)))
  let version = 0
  async function load() {
    const code = templateCode()
    const current = ++version
    if (!code || !monthlyTaskFieldDefinitions[code]) { fields.value = []; users.value = []; error.value = code ? "当前月度计划模板未配置可选展示字段。" : "月度计划缺少模板信息，无法加载展示字段。"; return }
    error.value = ""
    const fallback = monthlyTaskFieldDefinitions[code]!
    fields.value = fallback
    void listUserOptions().then(response => { if (current === version) users.value = response.items }).catch(() => { if (current === version) users.value = [] })
    try {
      const template = await getReportTemplate(code)
      if (current !== version) return
      const known = new Set(fallback.map(field => field.code))
      const configured = (template.fields || []).filter(field => known.has(field.field_code as MonthlyTaskFieldDefinition["code"]))
        .map(field => ({ code: field.field_code as MonthlyTaskFieldDefinition["code"], label: field.label, sort_order: Number(field.sort_order), default_visible: field.default_visible }))
        .filter(field => field.label && Number.isFinite(field.sort_order))
      const overrides = new Map(configured.map(field => [field.code, field]))
      fields.value = fallback.map(field => overrides.get(field.code) || field)
    } catch (reason) {
      if (current === version) error.value = reason instanceof Error ? reason.message : "字段配置加载失败"
    }
  }
  watch(templateCode, () => { columnsOpen.value = false; void load() }, { immediate: true })
  watch([availableFields, storageKey], ([options]) => {
    let stored: unknown
    try { stored = JSON.parse(localStorage.getItem(storageKey.value) || "null") } catch { stored = null }
    selected.value = options.filter(field => !Array.isArray(stored) || stored.includes(field.code)).map(field => field.code)
  }, { immediate: true })
  watch(selected, value => {
    try { localStorage.setItem(storageKey.value, JSON.stringify(value)) } catch { /* 浏览器禁用存储时仍允许切换列。 */ }
  }, { deep: true })
  return { users, columnsOpen, selected, availableFields, selectedFields, fieldError: error, reloadFields: load }
}
