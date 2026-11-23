import axios from "axios"

import type { ApiFailure } from "./types"

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly code = "UNKNOWN_ERROR",
    public readonly status?: number,
    public readonly details?: unknown,
  ) {
    super(message.replaceAll("角色", "职位"))
    this.name = "ApiError"
  }
}

export function normalizeApiError(error: unknown): ApiError {
  if (error instanceof ApiError) {
    return error
  }

  if (axios.isAxiosError<ApiFailure>(error)) {
    const payload = error.response?.data
    return new ApiError(
      payload?.error?.message || error.message || "后端服务请求失败",
      payload?.error?.code || "HTTP_ERROR",
      error.response?.status,
      payload?.error?.details,
    )
  }

  return new ApiError(error instanceof Error ? error.message : "发生未知错误")
}

export function getErrorMessage(error: unknown): string {
  return normalizeApiError(error).message
}

