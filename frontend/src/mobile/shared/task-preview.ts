import type { ComputedRef, InjectionKey } from "vue"
/** Limit only the referenced plan preview, never the editable task collection. */
export const taskPreviewLimitKey:InjectionKey<ComputedRef<number>>=Symbol('task-preview-limit')
