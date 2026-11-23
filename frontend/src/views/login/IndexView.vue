<script setup lang="ts">
import { reactive, ref } from "vue"
import { useRoute, useRouter } from "vue-router"

import dingchiLogo from "@/assets/brand/dingchi-logo.png"
import { useAuthStore } from "@/features/auth/store"

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()
const form = reactive({ username: "delivery.specialist", password: "aa123456" })
const showPassword = ref(false)
const localError = ref("")

async function handleSubmit() {
  localError.value = ""
  try {
    await authStore.signIn(form.username.trim(), form.password)
    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "/"
    await router.push(redirect)
  } catch (error) {
    localError.value = error instanceof Error ? error.message : "登录失败，请检查账号和密码。"
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-glow login-glow--one" />
    <div class="login-glow login-glow--two" />
    <section class="login-card">
      <div class="login-brand">
        <span class="login-mark">
          <img :src="dingchiLogo" alt="鼎驰" />
        </span>
        <div>
          <p class="login-overline">DINGCHI WORKSPACE</p>
          <h1>智能周报驾驶舱</h1>
          <p>聚焦本周进展 · 洞察风险 · 驱动下周行动</p>
        </div>
      </div>

      <div class="login-copy">
        <span>欢迎回来</span>
        <h2>登录工作台</h2>
        <p>使用企业账号进入周报填报和经营看板。</p>
      </div>

      <form class="login-form" @submit.prevent="handleSubmit">
        <label>
          <span>账号</span>
          <input v-model="form.username" class="field-control" autocomplete="username" placeholder="请输入账号" required />
        </label>
        <label>
          <span>密码</span>
          <div class="password-input">
            <input
              v-model="form.password"
              class="field-control"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              placeholder="请输入密码"
              required
            />
            <button class="password-toggle" type="button" @click="showPassword = !showPassword">
              {{ showPassword ? "隐藏" : "显示" }}
            </button>
          </div>
        </label>
        <p v-if="localError || authStore.errorMessage" class="login-error" role="alert">
          {{ localError || authStore.errorMessage }}
        </p>
        <button class="login-submit" type="submit" :disabled="authStore.isLoading">
          {{ authStore.isLoading ? "正在登录…" : "进入周报驾驶舱" }}
        </button>
      </form>

    </section>
    <p class="login-footer">DingChi Week Report · Local Development</p>
  </div>
</template>

<style scoped src="./IndexView.css"></style>
