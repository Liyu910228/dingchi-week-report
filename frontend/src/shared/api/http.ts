import axios, { type AxiosRequestConfig } from "axios"

import { createTraceId } from "@/utils/trace"

import { ApiError, normalizeApiError } from "./errors"
import type { ApiEnvelope } from "./types"

const timeout = Number(import.meta.env.VITE_API_TIMEOUT || 30000)
let redirectingToLogin = false

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  timeout: Number.isFinite(timeout) ? timeout : 30000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
})

http.interceptors.request.use((config) => {
  config.headers = config.headers ?? {}

  // 浏览器必须根据 FormData 自动生成 multipart boundary。axios 实例默认的
  // application/json 头如果继续保留，Django 将不会解析 request.FILES，
  // 于是明明选择了文件，后端仍会收到“请选择附件”。
  if (typeof FormData !== "undefined" && config.data instanceof FormData) {
    delete config.headers["Content-Type"]
    delete config.headers["content-type"]
  }

  const traceId = config.headers["X-Trace-ID"] ?? config.headers["x-trace-id"]
  if (!traceId) {
    config.headers["X-Trace-ID"] = createTraceId()
  }
  const accessToken = localStorage.getItem("dingchi.access_token")
  if (accessToken && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    const normalized = normalizeApiError(error)
    if (normalized.status === 401 && !/\/(?:mobile\/)?login\/?$/.test(window.location.pathname)) {
      localStorage.removeItem("dingchi.access_token")
      localStorage.removeItem("dingchi.session")
      const mobile = window.location.pathname.startsWith("/mobile")
      const login = `${import.meta.env.BASE_URL.replace(/\/$/, "")}${mobile ? "/mobile/login" : "/login"}`
      const redirect = window.location.pathname + window.location.search + window.location.hash
      if (!redirectingToLogin) {
        redirectingToLogin = true
        window.location.replace(`${login}?redirect=${encodeURIComponent(redirect)}`)
      }
      normalized.message = ""
    }
    return Promise.reject(normalized)
  },
)

export async function request<T>(config: AxiosRequestConfig): Promise<T> {
  const response = await http.request<ApiEnvelope<T>>(config)
  const payload = response.data

  if (!payload.success) {
    throw new ApiError(
      payload.error.message,
      payload.error.code,
      response.status,
      payload.error.details,
    )
  }

  return payload.data
}
