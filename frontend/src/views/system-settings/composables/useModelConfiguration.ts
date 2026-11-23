import { computed, reactive, ref } from "vue"

import { getModelConfiguration, testModelConfiguration, updateModelConfiguration } from "@/features/ai-config/api"
import type {
  ModelConfiguration,
  ModelConfigurationFormState,
  ModelConfigurationPayload,
  ModelConfigurationTestResult,
} from "@/features/ai-config/types"
import { getErrorMessage } from "@/shared/api/errors"

export function useModelConfiguration() {
  const configuration = ref<ModelConfiguration | null>(null)
  const testResult = ref<ModelConfigurationTestResult | null>(null)
  const form = reactive<ModelConfigurationFormState>({
    model: "",
    vision_model: "",
    base_url: "",
    api_key: "",
    is_enabled: true,
  })
  const isLoading = ref(false)
  const isSaving = ref(false)
  const isTesting = ref(false)
  const errorMessage = ref("")
  const successMessage = ref("")
  const isBusy = computed(() => isLoading.value || isSaving.value || isTesting.value)

  function applyConfiguration(value: ModelConfiguration) {
    configuration.value = value
    form.model = value.model
    form.vision_model = value.vision_model
    form.base_url = value.base_url
    form.api_key = ""
    form.is_enabled = value.is_enabled
  }

  function buildPayload(): ModelConfigurationPayload {
    const apiKey = form.api_key.trim()
    return {
      model: form.model.trim(),
      vision_model: form.vision_model.trim(),
      base_url: form.base_url.trim(),
      ...(apiKey ? { api_key: apiKey } : {}),
      is_enabled: form.is_enabled,
    }
  }

  function clearMessages() {
    errorMessage.value = ""
    successMessage.value = ""
  }

  async function load() {
    if (isBusy.value) return
    isLoading.value = true
    clearMessages()
    try {
      applyConfiguration(await getModelConfiguration())
    } catch (error) {
      errorMessage.value = getErrorMessage(error)
    } finally {
      isLoading.value = false
    }
  }

  async function save() {
    if (isBusy.value) return
    isSaving.value = true
    clearMessages()
    try {
      applyConfiguration(await updateModelConfiguration(buildPayload()))
      testResult.value = null
      successMessage.value = "模型配置已保存。"
    } catch (error) {
      errorMessage.value = getErrorMessage(error)
    } finally {
      isSaving.value = false
    }
  }

  async function test() {
    if (isBusy.value) return
    isTesting.value = true
    clearMessages()
    testResult.value = null
    try {
      const result = await testModelConfiguration(buildPayload())
      testResult.value = result
      if (result.success) successMessage.value = result.message || "模型连接测试成功。"
      else errorMessage.value = result.message || "模型连接测试失败。"
    } catch (error) {
      errorMessage.value = getErrorMessage(error)
    } finally {
      isTesting.value = false
    }
  }

  return {
    configuration,
    form,
    testResult,
    isLoading,
    isSaving,
    isTesting,
    isBusy,
    errorMessage,
    successMessage,
    load,
    save,
    test,
  }
}
