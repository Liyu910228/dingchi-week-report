export type ModelConfigurationSource = "database" | "environment"

export interface ModelConfiguration {
  model: string
  vision_model: string
  base_url: string
  has_api_key: boolean
  api_key_masked: string
  is_enabled: boolean
  source: ModelConfigurationSource
  updated_at: string | null
  last_test_status: string
  last_test_message: string
  last_tested_at: string | null
}

export interface ModelConfigurationPayload {
  model: string
  vision_model: string
  base_url: string
  api_key?: string
  is_enabled: boolean
}

export interface ModelConfigurationFormState {
  model: string
  vision_model: string
  base_url: string
  api_key: string
  is_enabled: boolean
}

export interface ModelConfigurationTestResult {
  success: boolean
  message: string
  model: string
  latency_ms: number
  reply: string
}
