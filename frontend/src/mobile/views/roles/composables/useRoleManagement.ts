import { ref } from "vue"

import { listDictionaryItems } from "@/mobile/features/dictionary"
import type { DictionaryItem } from "@/mobile/features/dictionary"
import { createRole, deleteRole, listGroups, listRoles, updateRole } from "@/mobile/features/directory/api"
import type { DirectoryGroup, DirectoryRole, RoleMutationPayload } from "@/mobile/features/directory/types"

function getErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback
}

export function useRoleManagement() {
  const roles = ref<DirectoryRole[]>([])
  const isLoading = ref(false)
  const isSaving = ref(false)
  const isDeleting = ref(false)
  const errorMessage = ref("")
  const successMessage = ref("")
  const scopeOptions = ref<DictionaryItem[]>([])
  const templateOptions = ref<DictionaryItem[]>([])
  const groupOptions = ref<DirectoryGroup[]>([])
  const isDictionaryLoading = ref(false)
  const dictionaryErrorMessage = ref("")

  async function loadRoles() {
    isLoading.value = true
    errorMessage.value = ""
    try {
      roles.value = (await listRoles()).items
    } catch (error: unknown) {
      errorMessage.value = getErrorMessage(error, "职位数据加载失败。")
    } finally {
      isLoading.value = false
    }
  }

  async function loadDictionaries() {
    isDictionaryLoading.value = true
    dictionaryErrorMessage.value = ""
    try {
      const [scopes, templates, groups] = await Promise.all([
        listDictionaryItems("role_scope"),
        listDictionaryItems("report_template"),
        listGroups(),
      ])
      scopeOptions.value = scopes.items
      templateOptions.value = templates.items
      groupOptions.value = groups.items
    } catch (error: unknown) {
      dictionaryErrorMessage.value = getErrorMessage(error, "静态配置加载失败，请联系管理员。")
    } finally {
      isDictionaryLoading.value = false
    }
  }

  async function saveRole(role: DirectoryRole | null, payload: RoleMutationPayload) {
    isSaving.value = true
    errorMessage.value = ""
    successMessage.value = ""
    try {
      if (role) await updateRole(role.id, payload)
      else await createRole(payload)
      successMessage.value = role ? "职位配置已更新。" : "职位已创建。"
      await loadRoles()
      return true
    } catch (error: unknown) {
      errorMessage.value = getErrorMessage(error, role ? "职位更新失败。" : "职位创建失败。")
      return false
    } finally {
      isSaving.value = false
    }
  }

  async function removeRole(role: DirectoryRole) {
    isDeleting.value = true
    errorMessage.value = ""
    successMessage.value = ""
    try {
      await deleteRole(role.id)
      successMessage.value = `职位“${role.role_name}”已删除。`
      await loadRoles()
      return true
    } catch (error: unknown) {
      errorMessage.value = getErrorMessage(error, "职位删除失败。")
      return false
    } finally {
      isDeleting.value = false
    }
  }

  return {
    roles,
    isLoading,
    isSaving,
    isDeleting,
    errorMessage,
    successMessage,
    scopeOptions,
    templateOptions,
    groupOptions,
    isDictionaryLoading,
    dictionaryErrorMessage,
    loadRoles,
    loadDictionaries,
    saveRole,
    removeRole,
  }
}
