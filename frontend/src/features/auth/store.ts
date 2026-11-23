import { computed, ref } from "vue"
import { defineStore } from "pinia"

import { getMe, login, logout, switchRole } from "./api"
import type { Role, Session, UserAccount } from "./types"

const TOKEN_KEY = "dingchi.access_token"
const SESSION_KEY = "dingchi.session"

function loadSession(): Session | null {
  const raw = localStorage.getItem(SESSION_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as Session
  } catch {
    localStorage.removeItem(SESSION_KEY)
    return null
  }
}

export const useAuthStore = defineStore("auth", () => {
  const session = ref<Session | null>(loadSession())
  const isBootstrapped = ref(false)
  const isLoading = ref(false)
  const errorMessage = ref("")

  const token = computed(() => session.value?.access_token || localStorage.getItem(TOKEN_KEY) || "")
  const user = computed<UserAccount | null>(() => session.value?.user || null)
  const roles = computed<Role[]>(() => session.value?.roles || [])
  const activeRole = computed<Role | null>(() => session.value?.active_role || null)
  const effectiveRole = computed<Role | null>(() => {
    const priority: Record<string, number> = { self: 0, team: 1, all: 2 }
    return [...roles.value].sort((a, b) => Number(b.role_code === "system_admin") - Number(a.role_code === "system_admin") || (priority[b.scope] || 0) - (priority[a.scope] || 0))[0] || null
  })
  const reportingRoles = computed(() => roles.value.filter(role => role.scope !== "all" && Boolean(role.report_template_code?.trim())))
  const isAuthenticated = computed(() => Boolean(token.value && user.value))

  function setSession(value: Session) {
    localStorage.setItem(TOKEN_KEY, value.access_token)
    localStorage.setItem(SESSION_KEY, JSON.stringify(value))
    session.value = value
  }

  function clear() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(SESSION_KEY)
    session.value = null
  }

  async function bootstrap() {
    if (isBootstrapped.value) return
    if (!token.value) {
      isBootstrapped.value = true
      return
    }
    const requestedToken = token.value
    try {
      const current = await getMe()
      if (token.value !== requestedToken) return
      const existing = session.value
      if (existing) {
        setSession({ ...existing, ...current })
      }
    } catch {
      if (token.value === requestedToken) clear()
    } finally {
      isBootstrapped.value = true
    }
  }

  async function signIn(username: string, password: string, roleCode?: string) {
    isLoading.value = true
    errorMessage.value = ""
    try {
      setSession(await login(username, password, roleCode))
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : "登录失败，请稍后重试。"
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function changeRole(roleCode: string) {
    isLoading.value = true
    errorMessage.value = ""
    try {
      setSession(await switchRole(roleCode))
    } catch (error) {
      errorMessage.value = error instanceof Error ? error.message : "职位切换失败。"
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function signOut() {
    try {
      if (token.value) await logout()
    } catch {
      // 即使网络不可用也清理本地令牌，避免将失效会话留在浏览器。
    } finally {
      clear()
    }
  }

  return {
    session,
    isBootstrapped,
    isLoading,
    errorMessage,
    token,
    user,
    roles,
    activeRole,
    effectiveRole,
    reportingRoles,
    isAuthenticated,
    bootstrap,
    setSession,
    signIn,
    changeRole,
    signOut,
    clear,
  }
})
