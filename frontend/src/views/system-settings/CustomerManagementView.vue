<script setup lang="ts">
import { onMounted, ref } from "vue"

import NoticeBridge from "@/components/feedback/NoticeBridge.vue"
import type { Customer, CustomerMutationPayload } from "@/features/dictionary"

import CustomerCatalog from "./components/CustomerCatalog.vue"
import CustomerDeleteDialog from "./components/CustomerDeleteDialog.vue"
import CustomerEditorDialog from "./components/CustomerEditorDialog.vue"
import CustomerPageHeader from "./components/CustomerPageHeader.vue"
import { useCustomerManagement } from "./composables/useCustomerManagement"

const customerManagement = useCustomerManagement()
const isEditorOpen = ref(false)
const editingCustomer = ref<Customer | null>(null)
const deletingCustomer = ref<Customer | null>(null)

function openCreateDialog() {
  editingCustomer.value = null
  isEditorOpen.value = true
}

function openEditDialog(customer: Customer) {
  editingCustomer.value = customer
  isEditorOpen.value = true
}

function closeEditorDialog() {
  if (!customerManagement.isSaving.value) isEditorOpen.value = false
}

async function submitCustomer(payload: CustomerMutationPayload) {
  const isSaved = await customerManagement.saveCustomer(editingCustomer.value, payload)
  if (isSaved) isEditorOpen.value = false
}

async function confirmDelete() {
  if (!deletingCustomer.value) return
  const isDeleted = await customerManagement.removeCustomer(deletingCustomer.value)
  if (isDeleted) deletingCustomer.value = null
}

onMounted(() => {
  void customerManagement.loadCustomers()
})
</script>

<template>
  <div class="customer-page">
    <CustomerPageHeader
      :total="customerManagement.customers.value.length"
      :is-loading="customerManagement.isLoading.value"
      @create="openCreateDialog"
    />

    <NoticeBridge
      :warning-message="customerManagement.errorMessage.value"
      :reminder-message="customerManagement.successMessage.value"
    />

    <CustomerCatalog
      :customers="customerManagement.customers.value"
      :is-loading="customerManagement.isLoading.value"
      @delete="deletingCustomer = $event"
      @edit="openEditDialog"
    />

    <CustomerEditorDialog
      :customer="editingCustomer"
      :is-saving="customerManagement.isSaving.value"
      :open="isEditorOpen"
      @close="closeEditorDialog"
      @submit="submitCustomer"
    />
    <CustomerDeleteDialog
      :customer="deletingCustomer"
      :is-deleting="customerManagement.isDeleting.value"
      :open="Boolean(deletingCustomer)"
      @close="deletingCustomer = null"
      @confirm="confirmDelete"
    />
  </div>
</template>

<style scoped src="./CustomerManagementView.css"></style>
