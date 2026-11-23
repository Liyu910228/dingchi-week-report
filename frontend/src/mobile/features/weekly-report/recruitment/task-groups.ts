import type { RecruitmentTaskDraft } from "./types"
import type { EditableTask, TaskTemplateOption } from "../task-editing"
import { groupKey as sharedKey, templateTask as fromTemplate, patchSharedTasks as patchShared, insertChild as insertShared } from "../task-groups"
export type RecruitmentSharedField = "dimension" | "customer_name" | "task_name" | "work_content"
export function groupKey(task: RecruitmentTaskDraft, field: RecruitmentSharedField) { return sharedKey(task, field) }
export function templateTask(template: TaskTemplateOption): Partial<RecruitmentTaskDraft> { return fromTemplate(template) }
export function patchSharedTasks(tasks: RecruitmentTaskDraft[], key: string, patch: Partial<EditableTask>) { return patchShared(tasks, key, patch) }
export function insertChild(tasks: RecruitmentTaskDraft[], index: number, task: RecruitmentTaskDraft, field?: RecruitmentSharedField) { return insertShared(tasks, index, task, field) }
