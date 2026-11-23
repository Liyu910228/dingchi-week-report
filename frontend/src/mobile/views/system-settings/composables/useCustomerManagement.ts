import { ref } from "vue"

import { createCustomer, deleteCustomer, listCustomers, updateCustomer } from "@/mobile/features/dictionary"
import type { Customer, CustomerMutationPayload } from "@/mobile/features/dictionary"

function getErrorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback
}

export function useCustomerManagement() {
  const customers = ref<Customer[]>([])
  const isLoading = ref(false)
  const isSaving = ref(false)
  const isDeleting = ref(false)
  const errorMessage = ref("")
  const successMessage = ref("")

  async function loadCustomers() {
    isLoading.value = true
    errorMessage.value = ""
    try {
      customers.value = (await listCustomers()).items
    } catch (error: unknown) {
      errorMessage.value = getErrorMessage(error, "客户数据加载失败。")
    } finally {
      isLoading.value = false
    }
  }

  async function saveCustomer(customer: Customer | null, payload: CustomerMutationPayload) {
    isSaving.value = true
    errorMessage.value = ""
    successMessage.value = ""
    try {
      if (customer) await updateCustomer(customer.id, payload)
      else await createCustomer(payload)
      successMessage.value = customer ? "客户已更新。" : "客户已创建。"
      await loadCustomers()
      return true
    } catch (error: unknown) {
      errorMessage.value = getErrorMessage(error, customer ? "客户更新失败。" : "客户创建失败。")
      return false
    } finally {
      isSaving.value = false
    }
  }

  async function removeCustomer(customer: Customer) {
    isDeleting.value = true
    errorMessage.value = ""
    successMessage.value = ""
    try {
      await deleteCustomer(customer.id)
      successMessage.value = `客户「${customer.dict_name}」已删除。`
      await loadCustomers()
      return true
    } catch (error: unknown) {
      errorMessage.value = getErrorMessage(error, "客户删除失败。")
      return false
    } finally {
      isDeleting.value = false
    }
  }

  return {
    customers,
    isLoading,
    isSaving,
    isDeleting,
    errorMessage,
    successMessage,
    loadCustomers,
    saveCustomer,
    removeCustomer,
  }
}
