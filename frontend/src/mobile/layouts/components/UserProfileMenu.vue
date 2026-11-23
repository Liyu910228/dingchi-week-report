<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue"
import { useRouter } from "vue-router"

import { useAppStore } from "@/app/stores/app"
import NoticeBridge from "@/mobile/components/feedback/NoticeBridge.vue"
import { useAuthStore } from "@/features/auth/store"
import ContentFontControl from "@/mobile/features/preferences/components/ContentFontControl.vue"
import {useContentTypography} from "@/mobile/features/preferences/useContentTypography"
import ChangePasswordDialog from "./ChangePasswordDialog.vue"

const appStore = useAppStore()
useContentTypography()
const authStore = useAuthStore()
const router = useRouter()
const menuElement = ref<HTMLElement | null>(null)
const isOpen = ref(false)
const isChangePasswordOpen = ref(false)
const roleNames = computed(() => authStore.roles.map(role => role.role_name).join(" / ") || "暂无职位")
const displayName = computed(() => {
  const rawName = authStore.user?.display_name?.trim() || "未登录"
  const nameParts = rawName.split(/[·•]/).map((part) => part.trim()).filter(Boolean)
  return nameParts[nameParts.length - 1] || rawName
})

function handleDocumentPointerDown(event: PointerEvent) {
  if (!isOpen.value || menuElement.value?.contains(event.target as Node)) return
  isOpen.value = false
}

function handleDocumentKeyDown(event: KeyboardEvent) {
  if (event.key === "Escape") isOpen.value = false
}

function openChangePassword() {
  isOpen.value = false
  isChangePasswordOpen.value = true
}

async function handleSignOut() {
  await authStore.signOut()
  isOpen.value = false
  await router.push("/mobile/login")
}

onMounted(() => {
  document.addEventListener("pointerdown", handleDocumentPointerDown)
  document.addEventListener("keydown", handleDocumentKeyDown)
})

onBeforeUnmount(() => {
  document.removeEventListener("pointerdown", handleDocumentPointerDown)
  document.removeEventListener("keydown", handleDocumentKeyDown)
})
</script>

<template>
  <div ref="menuElement" class="sidebar-profile">
    <button
      class="profile-trigger"
      :class="{ 'profile-trigger--open': isOpen }"
      type="button"
      :aria-expanded="isOpen"
      aria-haspopup="dialog"
      aria-label="个人信息"
      @click="isOpen = !isOpen"
    >
      <span class="profile-copy">
        <strong>个人信息</strong>
      </span>
      <span class="profile-caret" aria-hidden="true">›</span>
    </button>

    <Transition name="profile-popover">
      <section v-if="isOpen" class="profile-panel" role="dialog" aria-label="用户信息">
        <div class="profile-panel-head">
          <span class="profile-panel-avatar" :style="{ background: authStore.user?.avatar_color || '#16a6d8' }">
            {{ authStore.user?.display_name?.slice(-1) || "我" }}
          </span>
          <div>
            <strong>{{ displayName }}</strong>
            <small>{{ authStore.user?.employee_no || authStore.user?.username || "本地账号" }}</small>
          </div>
        </div>

        <div class="profile-role-section">
          <span class="profile-section-label">职位</span>
          <p class="profile-role-text">{{ roleNames }}</p>
        </div>

        <ContentFontControl />

        <NoticeBridge :warning-message="authStore.errorMessage" />

        <div class="profile-panel-actions">
          <button type="button" @click="appStore.toggleTheme">
            {{ appStore.theme === "light" ? "切换深色" : "切换浅色" }}
          </button>
          <button type="button" @click="openChangePassword">修改密码</button>
          <button class="profile-signout" type="button" @click="handleSignOut">退出登录</button>
        </div>
      </section>
    </Transition>

    <ChangePasswordDialog :open="isChangePasswordOpen" @close="isChangePasswordOpen = false" />
  </div>
</template>

<style scoped src="./UserProfileMenu.css"></style>
