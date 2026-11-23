import { encryptPassword } from "@/shared/security/password"

import { request } from "@/shared/api/http"

import type { Role, Session } from "./types"

/**
 * 用户登录：POST /v1/auth/login/（统一客户端拼接 /api）。
 * 请求：username、明文密码（函数内部先通过 RSA-OAEP-SHA256 加密）、可选 role_code。
 * 响应：Session，包含 Bearer 令牌、用户、全部角色和激活角色；错误：INVALID_REQUEST、AUTHENTICATION_FAILED。
 * 安全/追踪：加密失败直接阻止请求，http 层统一附加 X-Trace-ID；兼容：新增会话字段只增不删。
 */
export async function login(username: string, password: string, roleCode?: string): Promise<Session> {
  const encryptedPassword = await encryptPassword(password)
  return request<Session>({
    method: "POST",
    url: "/v1/auth/login/",
    data: { username, password: encryptedPassword, role_code: roleCode },
  })
}

/**
 * 获取当前会话：GET /v1/auth/me/；Bearer 认证、无参数、幂等。
 * 返回用户、角色集合和当前角色；错误：AUTHENTICATION_FAILED；X-Trace-ID 由共享 HTTP 层处理。
 */
export function getMe(): Promise<Pick<Session, "user" | "roles" | "active_role">> {
  return request<Pick<Session, "user" | "roles" | "active_role">>({
    method: "GET",
    url: "/v1/auth/me/",
  })
}

/**
 * 切换角色：POST /v1/auth/switch-role/；Bearer 认证，请求 role_code，返回新的 Session。
 * 仅允许已分配角色；错误：AUTHENTICATION_FAILED、FORBIDDEN；响应带 X-Trace-ID，字段向后兼容。
 */
export function switchRole(roleCode: string): Promise<Session> {
  return request<Session>({
    method: "POST",
    url: "/v1/auth/switch-role/",
    data: { role_code: roleCode },
  })
}

/**
 * 修改当前登录用户密码：POST /v1/auth/change-password/；Bearer 认证、幂等：否。
 * 请求：old_password、new_password（函数内部先通过 RSA-OAEP-SHA256 加密；
 * 新密码至少 8 位且不能与旧密码相同，由后端最终校验）。
 * 响应：完整的 Session（access_token、token_type、expires_in、user、roles、active_role），
 * 调用方需把整个 Session 写回本地 store 以使用新令牌继续访问，实现"无感续期"；
 * 旧令牌为 stateless 签名令牌，按 AUTH_TOKEN_MAX_AGE_SECONDS 自然过期，不会立即吊销。
 * 错误：INVALID_REQUEST（旧密码不正确、密码不合规）、AUTHENTICATION_FAILED（未登录）。
 * 安全/追踪：密码只以密文传输，http 层统一附加 X-Trace-ID；响应字段向后兼容。
 */
export async function changePassword(oldPassword: string, newPassword: string): Promise<Session> {
  const [oldCiphertext, newCiphertext] = await Promise.all([
    encryptPassword(oldPassword),
    encryptPassword(newPassword),
  ])
  return request<Session>({
    method: "POST",
    url: "/v1/auth/change-password/",
    data: { old_password: oldCiphertext, new_password: newCiphertext },
  })
}

/**
 * 注销：POST /v1/auth/logout/；Bearer 认证，无请求参数，客户端随后清除令牌。
 * 服务端令牌按配置过期；错误：AUTHENTICATION_FAILED；响应带 X-Trace-ID。
 */
export function logout(): Promise<{ logged_out: boolean }> {
  return request<{ logged_out: boolean }>({ method: "POST", url: "/v1/auth/logout/" })
}

export function roleLabel(role: Role | null | undefined): string {
  return role?.role_name || "未选择职位"
}
