<script setup lang="ts">
import BaseDialog from "@/mobile/components/overlay/BaseDialog.vue"
import type { DirectoryRole } from "@/mobile/features/directory/types"

withDefaults(
  defineProps<{
    open: boolean
    role?: DirectoryRole | null
    isDeleting?: boolean
  }>(),
  {
    role: null,
    isDeleting: false,
  },
)

defineEmits<{
  close: []
  confirm: []
}>()
</script>

<template>
  <BaseDialog
    :busy="isDeleting"
    :open="open"
    title="删除职位"
    width="480px"
    @close="$emit('close')"
  >
    <div v-if="role" class="delete-content">
      <p>
        确认删除职位“<strong>{{ role.role_name }}</strong>”吗？
      </p>
      <div class="role-summary">
        <span>职位编码</span>
        <strong>{{ role.role_code }}</strong>
      </div>
    </div>

    <template #actions>
      <button class="secondary-button" type="button" :disabled="isDeleting" @click="$emit('close')">
        取消
      </button>
      <button class="danger-button" type="button" :disabled="isDeleting" @click="$emit('confirm')">
        {{ isDeleting ? "删除中…" : "确认删除" }}
      </button>
    </template>
  </BaseDialog>
</template>

<style scoped src="./RoleDeleteDialog.css"></style>
