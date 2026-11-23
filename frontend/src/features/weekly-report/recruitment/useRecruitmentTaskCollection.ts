import { computed, nextTick, onMounted, ref, watch } from "vue"
import { listUserOptions } from "@/features/directory/api"
import type { DirectoryUserOption } from "@/features/directory/types"
import type { EditableTask } from "../task-editing"
import { expandTemplateTasks } from "../task-groups"
import { recruitmentTaskTemplates } from "./task-templates"
import { emptyRecruitmentTask, recruitmentTaskFieldDefinitions, type RecruitmentTaskDraft, type RecruitmentTaskFieldDefinition, type RecruitmentTaskColumn } from "./types"
import { insertChild, patchSharedTasks, templateTask, type RecruitmentSharedField } from "./task-groups"

export interface RecruitmentCollectionProps {
  title: string
  tasks: RecruitmentTaskDraft[]
  defaultOwnerId?: string
  ownerName?: string
  fieldDefinitions?: RecruitmentTaskFieldDefinition[]
}
export function useRecruitmentTaskCollection(props: RecruitmentCollectionProps, emit: (event: "update:tasks", tasks: RecruitmentTaskDraft[]) => void) {
  const quickFillOpen = ref(false)
  const columnsOpen = ref(false)
  const users = ref<DirectoryUserOption[]>([])
  const dimensionFilter = ref("")
  const plannedDateFilter = ref("")
  const taskPage = ref(1)
  const pageSize = 10
  const insertedKeys = ref(new Set<string>())
  const selectedColumns = ref<RecruitmentTaskColumn[]>([])
  const dimensionOptions = computed(() => [...new Set(props.tasks.map(task => task.dimension).filter(Boolean))])
  const filteredTaskEntries = computed(() => props.tasks.map((task, index) => ({ task, index })).filter(({ task }) =>
    insertedKeys.value.has(task.client_key) || ((!dimensionFilter.value || task.dimension === dimensionFilter.value) && (!plannedDateFilter.value || task.planned_completion_date === plannedDateFilter.value)),
  ))
  const totalPages = computed(() => Math.max(1, Math.ceil(filteredTaskEntries.value.length / pageSize)))
  const pagedTaskEntries = computed(() => filteredTaskEntries.value.slice((taskPage.value - 1) * pageSize, taskPage.value * pageSize))
  const availableFields = computed(() => (props.fieldDefinitions?.length ? props.fieldDefinitions : recruitmentTaskFieldDefinitions)
    .filter(field => field.code !== "dimension" && field.code !== "task_name").sort((a, b) => a.sort_order - b.sort_order))
  const selectedFields = computed(() => availableFields.value.filter(field => selectedColumns.value.includes(field.code)))
  const storageKey = "weekly-report:visible-columns:recruitment_v1:weekly:all-fields-v3"
  watch(availableFields, fields => {
    try {
      const stored: unknown = JSON.parse(localStorage.getItem(storageKey) || "null")
      selectedColumns.value = Array.isArray(stored) ? fields.filter(field => stored.includes(field.code)).map(field => field.code) : fields.map(field => field.code)
    } catch { selectedColumns.value = fields.map(field => field.code) }
  }, { immediate: true, deep: true })
  watch(selectedColumns, values => { try { localStorage.setItem(storageKey, JSON.stringify(values)) } catch { /* 存储不可用时保留当前选择。 */ } }, { deep: true })
  watch([dimensionFilter, plannedDateFilter], () => { insertedKeys.value.clear(); taskPage.value = 1 })
  watch(totalPages, value => { taskPage.value = Math.min(taskPage.value, value) })
  watch(dimensionOptions, values => { if (!values.includes(dimensionFilter.value)) dimensionFilter.value = "" })
  function newTask() { return { ...emptyRecruitmentTask(props.ownerName), owner_id: props.defaultOwnerId || null } }
  async function showTask(key: string) {
    await nextTick()
    taskPage.value = Math.floor(Math.max(0, filteredTaskEntries.value.findIndex(entry => entry.task.client_key === key)) / pageSize) + 1
  }
  function addTemplates(_: string, indexes: number[]) {
    const tasks = [...indexes].sort((a, b) => a - b).flatMap(index => expandTemplateTasks(() => ({ ...newTask(), ...templateTask(recruitmentTaskTemplates[index]!) })))
    for (const task of tasks) insertedKeys.value.add(task.client_key)
    emit("update:tasks", [...props.tasks, ...tasks])
    quickFillOpen.value = false
  }
  function insertTask(index: number, shared?: RecruitmentSharedField) {
    const task = newTask()
    insertedKeys.value.add(task.client_key)
    emit("update:tasks", insertChild(props.tasks, index, task, shared))
    void showTask(task.client_key)
  }
  function patchTask(key: string, value: Partial<EditableTask>) { emit("update:tasks", patchSharedTasks(props.tasks, key, value)) }
  function removeTask(index: number) { emit("update:tasks", props.tasks.filter((_, i) => i !== index)) }
  onMounted(async () => { try { users.value = (await listUserOptions()).items } catch { users.value = [] } })
  return { quickFillOpen, columnsOpen, users, dimensionFilter, plannedDateFilter, taskPage, pageSize, selectedColumns, dimensionOptions, filteredTaskEntries, totalPages, pagedTaskEntries, availableFields, selectedFields, addTemplates, insertTask, patchTask, removeTask }
}
