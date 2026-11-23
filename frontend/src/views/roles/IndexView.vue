<script setup lang="ts">
import { onMounted, ref } from "vue"

import { useAuthStore } from "@/features/auth/store"
import type { DirectoryRole, RoleMutationPayload } from "@/features/directory/types"
import NoticeBridge from "@/components/feedback/NoticeBridge.vue"

import RoleCatalog from "./components/RoleCatalog.vue"
import RoleDeleteDialog from "./components/RoleDeleteDialog.vue"
import RoleDetailDialog from "./components/RoleDetailDialog.vue"
import RoleEditorDialog from "./components/RoleEditorDialog.vue"
import RolePageHeader from "./components/RolePageHeader.vue"
import { useRoleManagement } from "./composables/useRoleManagement"

const authStore = useAuthStore()
const roleManagement = useRoleManagement()
const isEditorOpen = ref(false)
const viewingRole = ref<DirectoryRole | null>(null)
const editingRole = ref<DirectoryRole | null>(null)
const deletingRole = ref<DirectoryRole | null>(null)

function openCreateDialog() {
  editingRole.value = null
  isEditorOpen.value = true
}

function openEditDialog(role: DirectoryRole) {
  viewingRole.value = null
  editingRole.value = role
  isEditorOpen.value = true
}

function closeEditorDialog() {
  if (!roleManagement.isSaving.value) isEditorOpen.value = false
}

async function submitRole(payload: RoleMutationPayload) {
  const isSaved = await roleManagement.saveRole(editingRole.value, payload)
  if (isSaved) isEditorOpen.value = false
}

async function confirmDelete() {
  if (!deletingRole.value) return
  const isDeleted = await roleManagement.removeRole(deletingRole.value)
  if (isDeleted) deletingRole.value = null
}

onMounted(() => {
  void roleManagement.loadRoles()
  void roleManagement.loadDictionaries()
})
</script>

<template>
  <div class="roles-page">
    <RolePageHeader @create="openCreateDialog" />

    <NoticeBridge
      :warning-message="roleManagement.errorMessage.value"
      :reminder-message="roleManagement.successMessage.value"
    />
    <NoticeBridge :warning-message="roleManagement.dictionaryErrorMessage.value" />

    <RoleCatalog
      :active-role-code="authStore.effectiveRole?.role_code"
      :is-loading="roleManagement.isLoading.value"
      :roles="roleManagement.roles.value"
      :scope-options="roleManagement.scopeOptions.value"
      :template-options="roleManagement.templateOptions.value"
      :group-options="roleManagement.groupOptions.value"
      @delete="deletingRole = $event"
      @view="viewingRole = $event"
      @edit="openEditDialog"
    />

    <RoleDetailDialog
      :open="Boolean(viewingRole)" :role="viewingRole"
      :scope-options="roleManagement.scopeOptions.value"
      :template-options="roleManagement.templateOptions.value"
      :group-options="roleManagement.groupOptions.value"
      @close="viewingRole = null" @edit="openEditDialog"
    />
    <RoleEditorDialog
      :is-dictionary-loading="roleManagement.isDictionaryLoading.value"
      :is-saving="roleManagement.isSaving.value"
      :open="isEditorOpen"
      :role="editingRole"
      :scope-options="roleManagement.scopeOptions.value"
      :template-options="roleManagement.templateOptions.value"
      :group-options="roleManagement.groupOptions.value"
      @close="closeEditorDialog"
      @submit="submitRole"
    />
    <RoleDeleteDialog
      :is-deleting="roleManagement.isDeleting.value"
      :open="Boolean(deletingRole)"
      :role="deletingRole"
      @close="deletingRole = null"
      @confirm="confirmDelete"
    />
  </div>
</template>

<style scoped src="./IndexView.css"></style>
