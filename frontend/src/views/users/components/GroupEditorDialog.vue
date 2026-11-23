<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from "vue"

import NoticeBridge from "@/components/feedback/NoticeBridge.vue"
import BaseDialog from "@/components/overlay/BaseDialog.vue"
import GroupTreeSelect from "@/features/directory/components/GroupTreeSelect.vue"
import type { DirectoryGroup, GroupMutationPayload } from "@/features/directory/types"

const props = withDefaults(
  defineProps<{
    open: boolean
    group?: DirectoryGroup | null
    groups?: DirectoryGroup[]
    initialParentGroupId?: string | null
    isSaving?: boolean
  }>(),
  {
    group: null,
    groups: () => [],
    initialParentGroupId: null,
    isSaving: false,
  },
)

const emit = defineEmits<{
  close: []
  submit: [payload: GroupMutationPayload]
}>()

const isEditing = computed(() => Boolean(props.group))
const isCreatingChild = computed(() => !props.group && Boolean(props.initialParentGroupId))
const formError = ref("")
const groupCodeInput = ref<HTMLInputElement | null>(null)
const form = reactive<GroupMutationPayload>({
  group_code: "",
  group_name: "",
  description: "",
  parent_group_id: null,
})

const excludedParentIds = computed(() => {
  const excluded = new Set<string>()
  if (!props.group) return excluded
  const childrenMap = new Map<string, string[]>()
  for (const group of props.groups) {
    if (!group.parent_group_id) continue
    const children = childrenMap.get(group.parent_group_id) || []
    children.push(group.id)
    childrenMap.set(group.parent_group_id, children)
  }
  const visit = (id: string) => {
    if (excluded.has(id)) return
    excluded.add(id)
    for (const childId of childrenMap.get(id) || []) visit(childId)
  }
  visit(props.group.id)
  return excluded
})

const availableParentGroups = computed(() => props.groups.filter((group) => !excludedParentIds.value.has(String(group.id))))

watch(
  () => ({ open: props.open, group: props.group, initialParentGroupId: props.initialParentGroupId }),
  ({ open, group, initialParentGroupId }) => {
    if (!open) return
    Object.assign(
      form,
      group
        ? {
            group_code: group.group_code,
            group_name: group.group_name,
            description: group.description,
            parent_group_id: group.parent_group_id ? String(group.parent_group_id) : null,
          }
        : {
            group_code: "",
            group_name: "",
            description: "",
            parent_group_id: initialParentGroupId ? String(initialParentGroupId) : null,
          },
    )
    formError.value = ""
    void nextTick(() => groupCodeInput.value?.focus())
  },
  { immediate: true },
)

function submitForm() {
  const payload: GroupMutationPayload = {
    group_code: form.group_code.trim(),
    group_name: form.group_name.trim(),
    description: form.description.trim(),
    parent_group_id: isCreatingChild.value
      ? String(props.initialParentGroupId)
      : form.parent_group_id
        ? String(form.parent_group_id)
        : null,
  }
  if (!payload.group_code || !payload.group_name) {
    formError.value = "请填写分组编码和分组名称。"
    return
  }
  if (!/^[a-z][a-z0-9_]*$/.test(payload.group_code)) {
    formError.value = "分组编码必须以小写字母开头，只能包含小写字母、数字和下划线。"
    return
  }
  formError.value = ""
  emit("submit", payload)
}
</script>

<template>
  <BaseDialog
    :busy="isSaving"
    :open="open"
    overflow-visible
    :title="isEditing ? '编辑分组' : '新增分组'"
    width="700px"
    @close="emit('close')"
  >
    <form id="group-editor-form" class="group-form" @submit.prevent="submitForm">
      <NoticeBridge :warning-message="formError" />
      <div class="form-grid">
        <label>
          <span>分组编码</span>
          <input
            ref="groupCodeInput"
            v-model="form.group_code"
            autocomplete="off"
            maxlength="64"
            placeholder="delivery_center"
            :disabled="isEditing || isSaving"
          />
        </label>
        <label>
          <span>分组名称</span>
          <input v-model="form.group_name" maxlength="128" placeholder="交付中心" :disabled="isSaving" />
        </label>
        <div class="form-field">
          <span>上级分组</span>
          <GroupTreeSelect
            v-model="form.parent_group_id"
            :allow-empty="true"
            empty-label="顶级分组"
            :groups="availableParentGroups"
            :disabled="isSaving || isCreatingChild"
          />
        </div>
        <label>
          <span>分组说明</span>
          <input v-model="form.description" maxlength="255" placeholder="分组职责说明" :disabled="isSaving" />
        </label>
      </div>
    </form>
    <template #actions>
      <button class="secondary-button" type="button" :disabled="isSaving" @click="emit('close')">取消</button>
      <button class="primary-button" form="group-editor-form" type="submit" :disabled="isSaving">
        {{ isSaving ? "保存中…" : isEditing ? "保存修改" : "创建分组" }}
      </button>
    </template>
  </BaseDialog>
</template>

<style scoped src="./GroupEditorDialog.css"></style>
