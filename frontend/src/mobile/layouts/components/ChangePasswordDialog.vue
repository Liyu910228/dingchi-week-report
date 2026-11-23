<script setup lang="ts">
import { nextTick, reactive, ref, watch } from "vue"

import NoticeBridge from "@/mobile/components/feedback/NoticeBridge.vue"
import BaseDialog from "@/mobile/components/overlay/BaseDialog.vue"
import { changePassword } from "@/features/auth/api"
import { useAuthStore } from "@/features/auth/store"
import { useNoticeStore } from "@/app/stores/notice"

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const noticeStore = useNoticeStore()
const authStore = useAuthStore()
const isSaving = ref(false)
const formError = ref("")
const oldPasswordInput = ref<HTMLInputElement | null>(null)
const form = reactive({
  old_password: "",
  new_password: "",
  confirm_password: "",
})

watch(
  () => props.open,
  (open) => {
    if (!open) return
    form.old_password = ""
    form.new_password = ""
    form.confirm_password = ""
    formError.value = ""
    void nextTick(() => oldPasswordInput.value?.focus())
  },
  { immediate: true },
)

function validate(): string {
  if (!form.old_password || !form.new_password || !form.confirm_password) {
    return "请填写旧密码和新密码。"
  }
  if (form.new_password.length < 8) {
    return "新密码长度至少 8 位。"
  }
  if (form.new_password === form.old_password) {
    return "新密码不能与旧密码相同。"
  }
  if (form.new_password !== form.confirm_password) {
    return "两次输入的新密码不一致。"
  }
  return ""
}

async function submitForm() {
  const error = validate()
  if (error) {
    formError.value = error
    return
  }
  isSaving.value = true
  formError.value = ""
  try {
    const session = await changePassword(form.old_password, form.new_password)
    authStore.setSession(session)
    noticeStore.reminder("密码修改成功")
    emit("close")
  } catch (cause) {
    formError.value = cause instanceof Error ? cause.message : "密码修改失败，请稍后重试。"
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <BaseDialog
    :busy="isSaving"
    :open="open"
    title="修改密码"
    width="480px"
    @close="emit('close')"
  >
    <form id="change-password-form" class="password-form" @submit.prevent="submitForm">
      <NoticeBridge :warning-message="formError" />
      <label>
        <span>旧密码</span>
        <input
          ref="oldPasswordInput"
          v-model="form.old_password"
          autocomplete="current-password"
          type="password"
          :disabled="isSaving"
        />
      </label>
      <label>
        <span>新密码</span>
        <input
          v-model="form.new_password"
          autocomplete="new-password"
          maxlength="64"
          placeholder="至少 8 位"
          type="password"
          :disabled="isSaving"
        />
      </label>
      <label>
        <span>确认新密码</span>
        <input
          v-model="form.confirm_password"
          autocomplete="new-password"
          maxlength="64"
          type="password"
          :disabled="isSaving"
        />
      </label>
    </form>
    <template #actions>
      <button class="secondary-button" type="button" :disabled="isSaving" @click="emit('close')">取消</button>
      <button class="primary-button" form="change-password-form" type="submit" :disabled="isSaving">
        {{ isSaving ? "提交中…" : "确认修改" }}
      </button>
    </template>
  </BaseDialog>
</template>

<style scoped src="./ChangePasswordDialog.css"></style>
