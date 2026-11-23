<script setup lang="ts">
import CustomerSelect from "@/mobile/features/directory/components/CustomerSelect.vue"
import { computed, nextTick, reactive, ref, watch } from "vue"

import NoticeBridge from "@/mobile/components/feedback/NoticeBridge.vue"
import BaseDialog from "@/mobile/components/overlay/BaseDialog.vue"
import type { DictionaryItem } from "@/mobile/features/dictionary"
import GroupTreeSelect from "@/mobile/features/directory/components/GroupTreeSelect.vue"
import type { DirectoryGroup, DirectoryRole, RoleMutationPayload } from "@/mobile/features/directory/types"

const props = withDefaults(
  defineProps<{
    open: boolean
    role?: DirectoryRole | null
    isSaving?: boolean
    isDictionaryLoading?: boolean
    scopeOptions?: DictionaryItem[]
    templateOptions?: DictionaryItem[]
    groupOptions?: DirectoryGroup[]
  }>(),
  {
    role: null,
    isSaving: false,
    isDictionaryLoading: false,
    scopeOptions: () => [],
    templateOptions: () => [],
    groupOptions: () => [],
  },
)

const emit = defineEmits<{
  close: []
  submit: [payload: RoleMutationPayload]
}>()

const emptyForm = (): RoleMutationPayload => ({
  customer_ids: [],
  role_code: "",
  role_name: "",
  scope: props.scopeOptions[0]?.dict_code || "",
  report_template_code: "",
  role_group_code: "",
  description: "",
})

const form = reactive<RoleMutationPayload>(emptyForm())
const formError = ref("")
const roleCodeInput = ref<HTMLInputElement | null>(null)
const roleNameInput = ref<HTMLInputElement | null>(null)
const isEditing = computed(() => Boolean(props.role))

watch(
  () => ({ open: props.open, role: props.role }),
  ({ open, role }) => {
    if (!open) return
    Object.assign(form, role ? toForm(role) : emptyForm())
    formError.value = ""
    void nextTick(() => (role ? roleNameInput.value : roleCodeInput.value)?.focus())
  },
  { immediate: true },
)

watch(
  () => [props.scopeOptions, props.templateOptions, props.groupOptions],
  () => {
    if (props.open && !props.role) {
      if (!form.scope) form.scope = props.scopeOptions[0]?.dict_code || ""
    }
  },
  { deep: true },
)

function toForm(role: DirectoryRole): RoleMutationPayload {
  return {
    customer_ids: [...(role.customer_ids || [])],
    role_code: role.role_code,
    role_name: role.role_name,
    scope: role.scope,
    report_template_code: role.report_template_code,
    role_group_code: role.role_group_code,
    description: role.description,
  }
}

function submitForm() {
  const payload: RoleMutationPayload = {
    customer_ids: [...(form.customer_ids || [])],
    role_code: form.role_code.trim(),
    role_name: form.role_name.trim(),
    scope: form.scope,
    report_template_code: form.report_template_code.trim(),
    role_group_code: form.role_group_code,
    description: form.description.trim(),
  }

  if (!payload.role_code || !payload.role_name || !payload.scope) {
    formError.value = "请完整填写职位编码、职位名称和数据范围。"
    return
  }
  if (!props.scopeOptions.some((item) => item.dict_code === payload.scope)) {
    formError.value = "请选择有效的数据范围。"
    return
  }
  if (payload.report_template_code && !props.templateOptions.some((item) => item.dict_code === payload.report_template_code)) {
    formError.value = "请选择有效的周报模板。"
    return
  }
  if (payload.role_group_code && !props.groupOptions.some((item) => item.group_code === payload.role_group_code)) {
    formError.value = "请选择有效的职位分组。"
    return
  }
  if (!/^[a-z][a-z0-9_]*$/.test(payload.role_code)) {
    formError.value = "职位编码必须以小写字母开头，只能包含小写字母、数字和下划线。"
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
    :title="isEditing ? '编辑职位' : '新增职位'"
    width="920px"
    @close="$emit('close')"
  >
    <form id="role-editor-form" class="role-form" @submit.prevent="submitForm">
      <NoticeBridge :warning-message="formError" />

      <div class="form-grid">
        <label>
          <span>职位编码</span>
          <input
            ref="roleCodeInput"
            v-model="form.role_code"
            autocomplete="off"
            maxlength="64"
            placeholder="project_specialist"
            :disabled="isEditing || isSaving"
          />
        </label>

        <label>
          <span>职位名称</span>
          <input
            ref="roleNameInput"
            v-model="form.role_name"
            autocomplete="off"
            maxlength="128"
            placeholder="项目专员"
            :disabled="isSaving"
          />
        </label>

        <label>
          <span>数据范围</span>
          <select
            v-model="form.scope"
            :disabled="isSaving || isDictionaryLoading || !scopeOptions.length"
          >
            <option value="" disabled>
              {{ isDictionaryLoading ? "正在加载静态配置…" : "请选择数据范围" }}
            </option>
            <option v-for="item in scopeOptions" :key="item.id" :value="item.dict_code">
              {{ item.dict_name }}
            </option>
          </select>
        </label>

        <label>
          <span>周报模板</span>
          <select
            v-model="form.report_template_code"
            :disabled="isSaving || isDictionaryLoading"
          >
            <option value="">{{ isDictionaryLoading ? "正在加载静态配置…" : "无" }}</option>
            <option v-for="item in templateOptions" :key="item.id" :value="item.dict_code">
              {{ item.dict_name }}
            </option>
          </select>
        </label>

        <label>
          <span>职位分组</span>
          <GroupTreeSelect
            v-model="form.role_group_code"
            :allow-empty="true"
            :disabled="isSaving"
            empty-label="未分组"
            :groups="groupOptions"
            value-field="group_code"
          />
        </label>

        <div class="customer-field">
          <span>负责的客户</span>
          <CustomerSelect show-select-all v-model="form.customer_ids" :disabled="isSaving" />
        </div>
        <label class="description-field">
          <span>职位说明</span>
          <textarea
            v-model="form.description"
            maxlength="255"
            placeholder="说明职位职责与数据边界"
            rows="4"
            :disabled="isSaving"
          ></textarea>
          <small>{{ form.description.length }}/255</small>
        </label>
      </div>
    </form>

    <template #actions>
      <button class="secondary-button" type="button" :disabled="isSaving" @click="$emit('close')">
        取消
      </button>
      <button class="primary-button" form="role-editor-form" type="submit" :disabled="isSaving">
        {{ isSaving ? "保存中…" : isEditing ? "保存修改" : "创建职位" }}
      </button>
    </template>
  </BaseDialog>
</template>

<style scoped src="./RoleEditorDialog.css"></style>

