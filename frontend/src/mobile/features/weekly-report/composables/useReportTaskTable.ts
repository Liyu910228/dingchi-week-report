import { mobileStorage as localStorage } from "@/mobile/shared/storage"
import { computed, ref, watch } from "vue"

import {
  formatReportTaskField,
  normalizeReportTaskFields,
  reportTaskStatusLabel,
  reportTaskUpdatedAt,
} from "@/mobile/features/weekly-report/task-fields"
import type {
  ReportAttachment,
  ReportItem,
  ReportTemplateField,
} from "@/mobile/features/weekly-report/types"


export interface ReportTaskTableProps {
  items: ReportItem[]
  fields?: ReportTemplateField[] | null
  attachments?: ReportAttachment[]
  showColumnsButton?: boolean
  showCustomerTabs?: boolean
  preferenceKey?: string
  templateCode?: string
}

export function useReportTaskTable(props: ReportTaskTableProps) {
  const deliveryMode = computed(() => ["delivery_specialist_v1", "delivery_assistant_v1"].includes(props.templateCode || ""))
  const humanResourcesMode = computed(() => props.templateCode === "human_resources_v1")
  const recruitmentMode = computed(() => props.templateCode === "recruitment_v1")
  const salesMode = computed(() => ["ito_sales_v1", "innovation_sales_v1"].includes(props.templateCode || ""))
  const functionalMode = computed(() => props.templateCode === "functional_group_v1")
  const sharedMode = computed(() => deliveryMode.value || recruitmentMode.value || salesMode.value || functionalMode.value || humanResourcesMode.value)
  const activeCustomer = ref("")
  const customerKey = (item: ReportItem) => item.customer_id || item.customer_name_snapshot || "unassigned"
  const customers = computed(() => {
    const entries = new Map<string, string>()
    for (const item of props.items) entries.set(customerKey(item), item.customer_name_snapshot || "未选择客户")
    return [...entries].map(([id, name]) => ({ id, name })).sort((a, b) => a.name.localeCompare(b.name, "zh-CN"))
  })
  watch(customers, (tabs) => {
    if (!tabs.some((tab) => tab.id === activeCustomer.value)) activeCustomer.value = tabs[0]?.id || ""
  }, { immediate: true })
  watch(activeCustomer, () => { page.value = 1 })
  const columnsOpen = ref(false)
  const selectedCodes = ref<string[]>([])
  const detailOpen = ref(false)
  const detailItem = ref<ReportItem | null>(null)
  const page = ref(1)
  const pageSize = 10

  const availableFields = computed(() => normalizeReportTaskFields(props.fields).map(field => props.templateCode === "ito_sales_v1" && field.field_code === "customer_name" ? { ...field, label: "维度" } : field))
  const columnStorageKey = computed(
    () => `weekly-report:detail-visible-columns:${sharedMode.value ? "shared-v3:" : ""}${props.preferenceKey || "default"}`,
  )
  const primaryField = computed<ReportTemplateField | null>(() => {
    if (deliveryMode.value || functionalMode.value) return null
    if (humanResourcesMode.value && !props.fields?.length) return { field_code: "dimension", label: "模块", sort_order: 1, default_visible: true }
    const source = props.fields || []
    const dimension = source.find((field) => field.field_code === "dimension")
    const customerField = source.find((field) => field.field_code === "customer_name")
    const customer = customerField && props.templateCode === "ito_sales_v1" ? { ...customerField, label: "维度" } : customerField

    // 模板字段配置是列表布局的唯一依据。职能组模板不配置客户/维度时，
    // 不再渲染一个空的主字段列；否则表格会留下与客户列同宽的空白区域。
    if (source.length) return dimension || customer || null

    // 兼容接口暂未返回字段配置的旧数据：招聘报告仍使用维度，其他报告
    // 根据任务数据判断是否存在客户主字段。
    const looksLikeRecruitment = !dimension
      && props.items.length > 0
      && props.items.every((item) => !item.customer_name_snapshot)
      && props.items.some((item) =>
        /recruitment|recruit|招聘/i.test(
          `${item.section_code || ""} ${item.section_name_snapshot || ""}`,
        ),
      )
    if (looksLikeRecruitment) {
      return { field_code: "dimension", label: "维度", sort_order: 1, default_visible: true }
    }
    if (props.items.some((item) => Boolean(item.customer_name_snapshot))) {
      return { field_code: "customer_name", label: props.templateCode === "ito_sales_v1" ? "维度" : "客户", sort_order: 1, default_visible: true }
    }
    return null
  })
  const displayItems = computed(() =>
    props.items
      .filter((item) => !deliveryMode.value || customerKey(item) === activeCustomer.value)
      .map((item, index) => ({ item, index }))
      .sort(
        (left, right) =>
          // 与编辑页及保存载荷一致，客户/维度仅用于展示和筛选，不参与任务排序。
          left.item.sort_order - right.item.sort_order ||
          left.index - right.index,
      )
      .map(({ item }) => item),
  )
  const totalPages = computed(() => Math.max(1, Math.ceil(displayItems.value.length / pageSize)))
  const pagedItems = computed(() => {
    return displayItems.value.slice(0, page.value * pageSize)
  })
  const selectedFields = computed(() => {
    const selected = new Set(selectedCodes.value)
    return availableFields.value.filter((field) => selected.has(field.field_code))
  })

  watch(
    [availableFields, columnStorageKey],
    ([fields, storageKey]) => {
      const available = new Set(fields.map((field) => field.field_code))
      try {
        const stored = localStorage.getItem(storageKey)
        if (stored !== null) {
          const parsed: unknown = JSON.parse(stored)
          if (Array.isArray(parsed)) {
            selectedCodes.value = parsed.filter(
              (code): code is string => typeof code === "string" && available.has(code),
            )
            return
          }
        }
      } catch {
        try { localStorage.removeItem(storageKey) } catch { /* storage may be unavailable */ }
      }
      selectedCodes.value = fields
        .filter((field) => sharedMode.value || field.default_visible)
        .map((field) => field.field_code)
    },
    { immediate: true, deep: true },
  )

  watch(selectedCodes, (codes) => {
    try { localStorage.setItem(columnStorageKey.value, JSON.stringify(codes)) }
    catch { /* keep the table usable when browser storage is unavailable */ }
  })

  watch(totalPages, (value) => {
    if (page.value > value) page.value = value
  }, { immediate: true })

  function customerRowspan(index: number): number {
    if (recruitmentMode.value || humanResourcesMode.value || salesMode.value) {
      const rows = pagedItems.value
      const key = (row: ReportItem) => (salesMode.value ? row.customer_text_id : row.dimension_text_id) || row.id
      if (index > 0 && key(rows[index - 1]!) === key(rows[index]!)) return 0
      let count = 1
      while (index + count < rows.length && key(rows[index + count]!) === key(rows[index]!)) count++
      return count
    }
    if (!primaryField.value) return 1
    const current = primaryValue(pagedItems.value[index])
    if (index > 0 && primaryValue(pagedItems.value[index - 1]) === current) return 0

    let rowspan = 1
    while (
      index + rowspan < pagedItems.value.length
      && primaryValue(pagedItems.value[index + rowspan]) === current
    ) {
      rowspan += 1
    }
    return rowspan
  }

  function primaryValue(item: ReportItem | undefined): string {
    if (!item || !primaryField.value) return ""
    if (primaryField.value.field_code === "dimension") {
      return formatReportTaskField(item, "dimension")
    }
    return formatReportTaskField(item, "customer_name")
  }

  function statusClass(value: string | null | undefined): string {
    return value || "unknown"
  }

  function taskStatus(item: ReportItem): string {
    return item.on_time_status || "unknown"
  }

  function openTask(item: ReportItem) {
    detailItem.value = item
    detailOpen.value = true
  }

  function itemAttachments(item: ReportItem): ReportAttachment[] {
    return (props.attachments || []).filter((attachment) => attachment.relation_sub_id === item.id)
  }

  function openColumns() {
    columnsOpen.value = true
  }



  function sharedKey(item: ReportItem, work: boolean): string {
    const task = `${salesMode.value ? item.customer_text_id || item.id : recruitmentMode.value || humanResourcesMode.value ? item.dimension_text_id || item.id : ""}:${item.task_text_id || item.id}`
    return work ? `${task}:${item.work_content_text_id || item.id}` : task
  }
  function sharedRowspan(index: number, work = false): number {
    if (!sharedMode.value) return 1
    const rows = pagedItems.value
    const key = sharedKey(rows[index]!, work)
    if (index > 0 && sharedKey(rows[index - 1]!, work) === key) return 0
    let count = 1
    while (index + count < rows.length && sharedKey(rows[index + count]!, work) === key) count++
    return count
  }

  return { sharedMode, recruitmentMode, deliveryMode, customers, activeCustomer, columnsOpen, selectedCodes, detailOpen, detailItem, page, pageSize, availableFields, primaryField, displayItems, totalPages, pagedItems, selectedFields, sharedKey, customerRowspan, primaryValue, statusClass, taskStatus, openTask, itemAttachments, openColumns, sharedRowspan, formatReportTaskField, reportTaskStatusLabel, reportTaskUpdatedAt }
}
