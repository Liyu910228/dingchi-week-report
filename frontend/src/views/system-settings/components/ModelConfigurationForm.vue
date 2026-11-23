<script setup lang="ts">
import { computed } from "vue"

import type { ModelConfigurationFormState } from "@/features/ai-config/types"

const props = defineProps<{
  form: ModelConfigurationFormState
  hasApiKey: boolean
  apiKeyMasked: string
  isLoading: boolean
  isSaving: boolean
  isTesting: boolean
  isBusy: boolean
}>()

const emit = defineEmits<{
  save: []
  test: []
}>()

const apiKeyPlaceholder = computed(() =>
  props.hasApiKey
    ? `已保存：${props.apiKeyMasked || "密钥掩码不可用"}，留空保持不变`
    : "输入 API Key",
)
const canSubmit = computed(() =>
  Boolean(props.form.model.trim() && props.form.base_url.trim()) && !props.isBusy,
)
</script>

<template>
  <form class="model-form" @submit.prevent="emit('save')">
    <p v-if="isLoading" class="loading-state" role="status">正在加载模型配置...</p>
    <div class="form-grid">
      <label class="form-field">
        <span>主模型<span class="required-mark">*</span></span>
        <input
          v-model="form.model"
          class="field-control"
          type="text"
          required
          autocomplete="off"
          placeholder="例如 qwen-plus"
          :disabled="isBusy"
        />
      </label>

      <label class="form-field">
        <span>视觉模型</span>
        <input
          v-model="form.vision_model"
          class="field-control"
          type="text"
          autocomplete="off"
          placeholder="可选，用于图片理解"
          :disabled="isBusy"
        />
        <small>未配置已开启的 OCR Key 时用于图片理解；复杂图片仍可使用视觉模型。</small>
      </label>

      <label class="form-field form-field-wide">
        <span>Base URL<span class="required-mark">*</span></span>
        <input
          v-model="form.base_url"
          class="field-control"
          type="url"
          required
          autocomplete="off"
          placeholder="https://api.example.com/v1"
          :disabled="isBusy"
        />
      </label>

      <label class="form-field form-field-wide">
        <span>API Key</span>
        <input
          v-model="form.api_key"
          class="field-control"
          type="password"
          autocomplete="new-password"
          :placeholder="apiKeyPlaceholder"
          :disabled="isBusy"
        />
        <small>不会回显原始密钥；已保存密钥时，留空表示保持不变。</small>
      </label>

      <label class="enable-field form-field-wide">
        <span>
          <strong>启用 AI 服务</strong>
          <small>关闭后，AI 助手将不可用。</small>
        </span>
        <input v-model="form.is_enabled" type="checkbox" role="switch" :disabled="isBusy" />
      </label>
    </div>

    <div class="form-actions">
      <button class="primary-button" type="submit" :disabled="!canSubmit">
        {{ isSaving ? "保存中..." : "保存" }}
      </button>
      <button class="secondary-button" type="button" :disabled="!canSubmit" @click="emit('test')">
        {{ isTesting ? "测试中..." : "测试连通性" }}
      </button>
    </div>
  </form>
</template>

<style scoped src="./ModelConfigurationForm.css"></style>
