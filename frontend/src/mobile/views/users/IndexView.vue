<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue"

import {
  createGroup,
  createUser,
  deleteGroup,
  deleteUser,
  listGroups,
  listRoles,
  listUsers,
  updateGroup,
  updateUser,
} from "@/mobile/features/directory/api"
import type {
  DirectoryGroup,
  DirectoryRole,
  DirectoryUser,
  GroupMutationPayload,
  UserMutationPayload,
} from "@/mobile/features/directory/types"
import { encryptPassword } from "@/shared/security/password"
import GroupTreeSelect from "@/mobile/features/directory/components/GroupTreeSelect.vue"
import OrganizationChart from "@/mobile/features/directory/components/OrganizationChart.vue"
import NoticeBridge from "@/mobile/components/feedback/NoticeBridge.vue"

import ConfirmDeleteDialog from "./components/ConfirmDeleteDialog.vue"
import GroupEditorDialog from "./components/GroupEditorDialog.vue"
import GroupManagementDialog from "./components/GroupManagementDialog.vue"
import UserDetailDialog from "./components/UserDetailDialog.vue"
import UserEditorDialog from "./components/UserEditorDialog.vue"

const users = ref<DirectoryUser[]>([])
const groups = ref<DirectoryGroup[]>([])
const roles = ref<DirectoryRole[]>([])
const isLoading = ref(true)
const isSaving = ref(false)
const isDeleting = ref(false)
const isGroupManagementOpen = ref(false)
const isGroupEditorOpen = ref(false)
const editingGroup = ref<DirectoryGroup | null>(null)
const newGroupParentId = ref<string | null>(null)
const isUserEditorOpen = ref(false)
const editingUser = ref<DirectoryUser | null>(null)
const viewingUser = ref<DirectoryUser | null>(null)
const deletingTarget = ref<
  | { kind: "group"; item: DirectoryGroup }
  | { kind: "user"; item: DirectoryUser }
  | null
>(null)
const errorMessage = ref("")
const successMessage = ref("")
const filters = reactive({ role_code: "", group_id: "", keyword: "" })

const roleName = (code: string) => roles.value.find((role) => role.role_code === code)?.role_name || code
const usersByGroup = computed(() => {
  const map = new Map<string, DirectoryUser[]>()
  for (const user of users.value) {
    const key = user.group_id ? String(user.group_id) : ""
    map.set(key, [...(map.get(key) || []), user])
  }
  return map
})
const ungroupedUsers = computed(() => usersByGroup.value.get("") || [])

const deleteTitle = computed(() => (deletingTarget.value?.kind === "group" ? "删除分组" : "删除用户"))
const deleteMessage = computed(() => {
  const target = deletingTarget.value
  if (!target) return ""
  if (target.kind === "group") return `确认删除分组“${target.item.group_name}”吗？有下级分组或在职成员时无法删除。`
  return `确认删除用户“${target.item.display_name}”吗？删除后该用户将无法登录，历史周报会保留；仍有直属下属时无法删除。`
})

function messageFromError(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback
}

async function load() {
  isLoading.value = true
  errorMessage.value = ""
  try {
    const [userData, groupData, roleData] = await Promise.all([
      listUsers(filters),
      listGroups(),
      listRoles(),
    ])
    users.value = userData.items
    groups.value = groupData.items
    roles.value = roleData.items
  } catch (error) {
    errorMessage.value = messageFromError(error, "组织数据加载失败。")
  } finally {
    isLoading.value = false
  }
}

function openCreateGroup(parentGroupId: string | null = null) {
  editingGroup.value = null
  newGroupParentId.value = parentGroupId
  isGroupEditorOpen.value = true
}

function openEditGroup(group: DirectoryGroup) {
  editingGroup.value = group
  newGroupParentId.value = null
  isGroupEditorOpen.value = true
}

function closeGroupEditor() {
  if (!isSaving.value) isGroupEditorOpen.value = false
}

async function submitGroup(payload: GroupMutationPayload) {
  isSaving.value = true
  errorMessage.value = ""
  try {
    if (editingGroup.value) await updateGroup(editingGroup.value.id, payload)
    else await createGroup(payload)
    successMessage.value = editingGroup.value ? "分组已更新。" : "分组已创建。"
    isGroupEditorOpen.value = false
    await load()
  } catch (error) {
    errorMessage.value = messageFromError(error, "分组保存失败。")
  } finally {
    isSaving.value = false
  }
}

function openCreateUser() {
  editingUser.value = null
  isUserEditorOpen.value = true
}

function openEditUser(user: DirectoryUser) {
  viewingUser.value = null
  editingUser.value = user
  isUserEditorOpen.value = true
}

function closeUserEditor() {
  if (!isSaving.value) isUserEditorOpen.value = false
}

async function submitUser(payload: UserMutationPayload) {
  isSaving.value = true
  errorMessage.value = ""
  try {
    const commonPayload = {
      username: payload.username,
      display_name: payload.display_name,
      email: payload.email,
      phone: payload.phone,
      group_id: payload.group_id || null,
      manager_id: payload.manager_ids?.[0] || null,
      manager_ids: payload.manager_ids || [],
      monthly_approver_ids: [...(payload.monthly_approver_ids || [])],
      shared_user_ids: [...(payload.shared_user_ids || [])],
      role_customer_ids: payload.role_customer_ids || {},
      role_codes: payload.role_codes,
      status: payload.status || "active",
    }
    const encryptedPassword = payload.password ? await encryptPassword(payload.password) : ""
    if (editingUser.value) {
      await updateUser(editingUser.value.id, {
        ...commonPayload,
        ...(encryptedPassword ? { password: encryptedPassword } : {}),
      })
    } else {
      if (!encryptedPassword) throw new Error("请设置初始密码。")
      await createUser({ ...commonPayload, password: encryptedPassword })
    }
    successMessage.value = editingUser.value ? "用户已更新。" : "用户已创建。"
    isUserEditorOpen.value = false
    await load()
  } catch (error) {
    errorMessage.value = messageFromError(error, "用户保存失败。")
  } finally {
    isSaving.value = false
  }
}

function requestDeleteGroup(group: DirectoryGroup) {
  deletingTarget.value = { kind: "group", item: group }
}

function requestDeleteUser(user: DirectoryUser) {
  deletingTarget.value = { kind: "user", item: user }
}

async function confirmDelete() {
  const target = deletingTarget.value
  if (!target) return
  isDeleting.value = true
  errorMessage.value = ""
  try {
    if (target.kind === "group") await deleteGroup(target.item.id)
    else await deleteUser(target.item.id)
    successMessage.value = target.kind === "group" ? "分组已删除。" : "用户已删除。"
    deletingTarget.value = null
    await load()
  } catch (error) {
    errorMessage.value = messageFromError(error, "删除失败。")
  } finally {
    isDeleting.value = false
  }
}

onMounted(() => void load())
</script>

<template>
  <div class="users-page">
    <section class="dashboard-card directory-card">
      <div class="directory-hero">
        <div>
          <h1>用户与组织</h1>
          <p>维护人员、职位、分组和上下级关系，周报权限会随组织关系自动计算。</p>
        </div>
        <div class="hero-actions">
          <button class="ghost-button" type="button" @click="isGroupManagementOpen = true">分组管理</button>
          <button class="primary-button" type="button" @click="openCreateUser">新增用户</button>
        </div>
      </div>

      <NoticeBridge :warning-message="errorMessage" :reminder-message="successMessage" />

      <div class="directory-heading">
        <h2>人员目录</h2>
        <div class="filter-row">
          <input
            v-model="filters.keyword"
            class="user-filter-input"
            type="search"
            aria-label="搜索用户"
            placeholder="登录账号/工号/用户名/邮箱/手机号"
            @keyup.enter="load"
          />
          <select v-model="filters.role_code" aria-label="按职位筛选" @change="load">
            <option value="">全部职位</option>
            <option v-for="role in roles" :key="role.id" :value="role.role_code">{{ role.role_name }}</option>
          </select>
          <GroupTreeSelect
            v-model="filters.group_id"
            aria-label="按分组筛选"
            :groups="groups"
            empty-label="全部分组"
            @update:model-value="load"
          />
          <button class="primary-button" type="button" :disabled="isLoading" @click="load">查询</button>
        </div>
      </div>

      <div v-if="isLoading" class="organization-loading">正在加载…</div>
      <OrganizationChart v-else :collapsible="true" :groups="groups">
        <template #node="{ group, isExpanded }">
          <strong class="organization-group-name">{{ group.group_name }}</strong>
          <span class="organization-member-count">{{ usersByGroup.get(String(group.id))?.length || 0 }} 人</span>
          <div
            v-if="isExpanded && usersByGroup.get(String(group.id))?.length"
            class="organization-members"
            @click.stop
          >
            <article
              v-for="user in usersByGroup.get(String(group.id))"
              :key="user.id"
              class="organization-member"
              role="button"
              tabindex="0"
              @click="viewingUser = user"
              @keydown.enter.prevent="viewingUser = user"
              @keydown.space.prevent="viewingUser = user"
            >
              <span class="person-avatar" :style="{ background: user.avatar_color || '#2f80ed' }">{{ user.display_name.slice(0, 1) }}</span>
              <span class="organization-member__identity">
                <strong>{{ user.display_name }}</strong>
                <small>{{ user.role_codes.map(roleName).join('、') }}</small>
              </span>
              <span class="organization-member__actions">
                <button type="button" @click.stop="openEditUser(user)">编辑</button>
                <button class="is-danger" type="button" @click.stop="requestDeleteUser(user)">删除</button>
              </span>
            </article>
          </div>
        </template>
      </OrganizationChart>

      <section v-if="ungroupedUsers.length" class="ungrouped-users">
        <h3>未分组人员</h3>
        <div class="ungrouped-users__list">
          <article
            v-for="user in ungroupedUsers"
            :key="user.id"
            class="ungrouped-user"
            role="button"
            tabindex="0"
            @click="viewingUser = user"
            @keydown.enter.prevent="viewingUser = user"
            @keydown.space.prevent="viewingUser = user"
          >
            <span class="person-avatar" :style="{ background: user.avatar_color || '#2f80ed' }">
              {{ user.display_name.slice(0, 1) }}
            </span>
            <span class="ungrouped-user__identity">
              <strong>{{ user.display_name }}</strong>
              <small>{{ user.username }}</small>
            </span>
            <span class="ungrouped-user__actions">
              <button type="button" @click.stop="openEditUser(user)">编辑</button>
              <button class="is-danger" type="button" @click.stop="requestDeleteUser(user)">删除</button>
            </span>
          </article>
        </div>
      </section>
    </section>

    <GroupManagementDialog
      :groups="groups"
      :is-saving="isSaving"
      :open="isGroupManagementOpen"
      @close="isGroupManagementOpen = false"
      @create="openCreateGroup"
      @delete="requestDeleteGroup"
      @edit="openEditGroup"
    />
    <GroupEditorDialog
      :group="editingGroup"
      :groups="groups"
      :initial-parent-group-id="newGroupParentId"
      :is-saving="isSaving"
      :open="isGroupEditorOpen"
      @close="closeGroupEditor"
      @submit="submitGroup"
    />
    <UserEditorDialog
      :groups="groups"
      :is-saving="isSaving"
      :open="isUserEditorOpen"
      :roles="roles"
      :user="editingUser"
      :users="users"
      @close="closeUserEditor"
      @submit="submitUser"
    />
    <UserDetailDialog :open="Boolean(viewingUser)" :user="viewingUser" :users="users" @close="viewingUser = null" @edit="openEditUser" />
    <ConfirmDeleteDialog
      :is-deleting="isDeleting"
      :message="deleteMessage"
      :open="Boolean(deletingTarget)"
      :title="deleteTitle"
      @close="deletingTarget = null"
      @confirm="confirmDelete"
    />
  </div>
</template>

<style scoped src="./IndexView.css"></style>
