import type { HumanResourcesTaskDraft } from "./types"
import type { EditableTask, TaskTemplateOption } from "../task-editing"
import { groupKey as sharedKey, templateTask as fromTemplate, patchSharedTasks as patchShared, insertChild as insertShared } from "../task-groups"
export type HumanResourcesSharedField = "dimension" | "customer_name" | "task_name" | "work_content"
export function groupKey(task: HumanResourcesTaskDraft, field: HumanResourcesSharedField) { return sharedKey(task, field) }
export function templateTask(template: TaskTemplateOption): Partial<HumanResourcesTaskDraft> { return fromTemplate(template) }
export function patchSharedTasks(tasks: HumanResourcesTaskDraft[], key: string, patch: Partial<EditableTask>) { return patchShared(tasks, key, patch) }
export function insertChild(tasks: HumanResourcesTaskDraft[], index: number, task: HumanResourcesTaskDraft, field?: HumanResourcesSharedField) { return insertShared(tasks, index, task, field) }
