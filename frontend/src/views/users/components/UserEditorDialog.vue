<script setup lang="ts">
import UserCustomerAssignments from "@/features/directory/components/UserCustomerAssignments.vue"
import { computed, nextTick, reactive, ref, watch } from "vue"
import NoticeBridge from "@/components/feedback/NoticeBridge.vue"
import BaseDialog from "@/components/overlay/BaseDialog.vue"
import PersonSelect from "@/features/directory/components/PersonSelect.vue"
import GroupTreeSelect from "@/features/directory/components/GroupTreeSelect.vue"
import type {
  DirectoryGroup,
  DirectoryRole,
  DirectoryUser,
  UserMutationPayload,
} from "@/features/directory/types"
const props = withDefaults(
  defineProps<{
    open: boolean
    user?: DirectoryUser | null
    users?: DirectoryUser[]
    groups?: DirectoryGroup[]
    roles?: DirectoryRole[]
    isSaving?: boolean
  }>(),
  {
    user: null,
    users: () => [],
    groups: () => [],
    roles: () => [],
    isSaving: false,
  },
)
const emit = defineEmits<{
  close: []
  submit: [payload: UserMutationPayload]
}>()
const isEditing = computed(() => Boolean(props.user))
const formError = ref("")
const displayNameInput = ref<HTMLInputElement | null>(null)
const form = reactive<UserMutationPayload>({
  username: "",
  employee_no: "",
  display_name: "",
  email: "",
  phone: "",
  password: "",
  group_id: null,
  manager_id: null,
  manager_ids: [],
  shared_user_ids: [],
  monthly_approver_ids: [],
  role_customer_ids: {},
  role_codes: [],
  status: "active",
})
const managerSelection = computed({
  get: () => form.manager_ids || [],
  set: (value: string | string[]) => { form.manager_ids = Array.isArray(value) ? value : value ? [value] : [] },
})
const monthlyApproverSelection = computed({
  get: () => form.monthly_approver_ids || [],
  set: (value: string | string[]) => { form.monthly_approver_ids = Array.isArray(value) ? value : value ? [value] : [] },
})
const sharedUserSelection = computed({
  get: () => form.shared_user_ids || [],
  set: (value: string | string[]) => { form.shared_user_ids = Array.isArray(value) ? value : value ? [value] : [] },
})
const availableManagers = computed(() => props.users.filter((item) => item.id !== props.user?.id))
watch(
  () => [props.open, props.user?.id] as const,
  ([open]) => {
    if (!open) return
    const user = props.user, roles = props.roles
    Object.assign(
      form,
      user
        ? {
            username: user.username,
            employee_no: user.employee_no,
            display_name: user.display_name,
            email: user.email,
            phone: user.phone || "",
            password: "",
            group_id: user.group_id,
            manager_id: user.manager_id,
            shared_user_ids: [...(user.shared_user_ids || [])],
            monthly_approver_ids: [...(user.monthly_approver_ids || [])],
            manager_ids: user.manager_ids?.length ? [...user.manager_ids] : user.manager_id ? [user.manager_id] : [],
            role_customer_ids: JSON.parse(JSON.stringify(user.role_customer_ids || {})),
            role_codes: [...user.role_codes],
            status: user.status,
          }
        : {
            username: "",
            employee_no: "",
            display_name: "",
            email: "",
            phone: "",
            password: "",
            group_id: null,
            manager_id: null,
            manager_ids: [],
            shared_user_ids: [],
            monthly_approver_ids: [],
            role_customer_ids: {},
            role_codes: roles[0] ? [roles[0].role_code] : [],
            status: "active",
          },
    )
    formError.value = ""
    void nextTick(() => displayNameInput.value?.focus())
  },
  { immediate: true },
)
function toggleRole(roleCode: string) {
  form.role_codes = form.role_codes.includes(roleCode)
    ? form.role_codes.filter((item) => item !== roleCode)
    : [...form.role_codes, roleCode]
}
function submitForm() {
  const payload: UserMutationPayload = {
    username: form.username.trim(),
    employee_no: form.employee_no?.trim() || undefined,
    display_name: form.display_name.trim(),
    email: form.email.trim(),
    phone: form.phone.trim(),
    password: form.password?.trim() || undefined,
    group_id: form.group_id || null,
    manager_id: form.manager_ids?.[0] || null,
    manager_ids: [...(form.manager_ids || [])],
    shared_user_ids: [...(form.shared_user_ids || [])],
    monthly_approver_ids: [...(form.monthly_approver_ids || [])],
    role_customer_ids: JSON.parse(JSON.stringify(form.role_customer_ids || {})),
    role_codes: [...form.role_codes],
    status: form.status || "active",
  }
  if (!payload.username || !payload.display_name) {
    formError.value = "请填写登录账号和姓名。"
    return
  }
  if (!isEditing.value && !payload.password) {
    formError.value = "请设置初始密码。"
    return
  }
  if (!payload.role_codes.length) {
    formError.value = "请至少选择一个职位。"
    return
  }
  if (payload.email && !/^\S+@\S+\.\S+$/.test(payload.email)) {
    formError.value = "请输入有效的邮箱地址。"
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
    :title="isEditing ? '编辑用户' : '新增用户'"
    width="860px"
    @close="emit('close')"
  >
    <form id="user-editor-form" class="user-form" @submit.prevent="submitForm">
      <NoticeBridge :warning-message="formError" />
      <div class="form-grid">
        <label>
          <span>登录账号</span>
          <input v-model="form.username" autocomplete="off" maxlength="64" placeholder="zhangsan" :disabled="isEditing || isSaving" />
        </label>
        <label v-if="isEditing">
          <span>工号</span>
          <input
            v-model="form.employee_no"
            autocomplete="off"
            maxlength="64"
            readonly
            :disabled="isSaving"
          />
        </label>
        <label>
          <span>姓名</span>
          <input ref="displayNameInput" v-model="form.display_name" maxlength="128" placeholder="张三" :disabled="isSaving" />
        </label>
        <label>
          <span>邮箱</span>
          <input v-model="form.email" autocomplete="email" maxlength="254" placeholder="name@example.com" type="email" :disabled="isSaving" />
        </label>
        <label>
          <span>手机号</span>
          <input v-model="form.phone" autocomplete="tel" maxlength="32" placeholder="请输入手机号" type="tel" :disabled="isSaving" />
        </label>
        <label>
          <span>{{ isEditing ? "重置密码" : "初始密码" }}</span>
          <input v-model="form.password" autocomplete="new-password" placeholder="请输入密码" type="password" :disabled="isSaving" />
        </label>
        <label>
          <span>所属分组</span>
          <GroupTreeSelect v-model="form.group_id" :disabled="isSaving" :groups="groups" />
        </label>
        <div class="person-field">
          <span>直属上级</span>
          <PersonSelect v-model="managerSelection" :users="availableManagers" :disabled="isSaving" multiple aria-label="直属上级" />
        </div>
        <div class="person-field">
          <span>月报审批人</span>
          <PersonSelect v-model="monthlyApproverSelection" :users="availableManagers" :disabled="isSaving" multiple ordered aria-label="月报审批顺序" />
          <small>按选择顺序依次审批；不选则提交后直接通过。</small>
        </div>
        <div class="person-field">
          <span>负责的客户</span>
          <UserCustomerAssignments v-model="form.role_customer_ids" :roles="roles" :role-codes="form.role_codes" :disabled="isSaving" />
        </div>
        <label v-if="isEditing">
          <span>账号状态</span>
          <select v-model="form.status" :disabled="isSaving">
            <option value="active">在职</option>
            <option value="inactive">停用</option>
          </select>
        </label>
        <div class="person-field">
          <span>共享用户</span>
          <PersonSelect v-model="sharedUserSelection" :users="availableManagers" :disabled="isSaving" multiple aria-label="共享用户" />
        </div>
        <fieldset class="role-fieldset">
          <legend>职位</legend>
          <label v-for="role in roles" :key="role.id" class="role-option">
            <input :checked="form.role_codes.includes(role.role_code)" type="checkbox" @change="toggleRole(role.role_code)" />
            <span>{{ role.role_name }}</span>
          </label>
          <p v-if="!roles.length" class="role-empty">暂无可用职位</p>
        </fieldset>
      </div>
    </form>
    <template #actions>
      <button class="secondary-button" type="button" :disabled="isSaving" @click="emit('close')">取消</button>
      <button class="primary-button" form="user-editor-form" type="submit" :disabled="isSaving">
        {{ isSaving ? "保存中…" : isEditing ? "保存修改" : "创建用户" }}
      </button>
    </template>
  </BaseDialog>
</template>
<style scoped src="./UserEditorDialog.css"></style>
