<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue"

import {
  createOCRKey,
  deleteOCRKey,
  getOCRKeys,
  setOCRKeyEnabled,
} from "@/features/ai-config/api"
import type { OCRKeyItem, OCRProvider } from "@/features/ai-config/types"
import { getErrorMessage } from "@/shared/api/errors"

const items = ref<OCRKeyItem[]>([])
const form = reactive({
  provider: "mineru" as OCRProvider,
  label: "",
  app_id: "",
  api_key: "",
  secret_key: "",
  is_enabled: true,
})
const isLoading = ref(false)
const isAdding = ref(false)
const busyId = ref("")
const errorMessage = ref("")
const successMessage = ref("")
const enabledCount = computed(() => items.value.filter((item) => item.is_enabled).length)
const canSubmit = computed(() => {
  if (!form.api_key.trim() || isAdding.value) return false
  return form.provider !== "baidu" || Boolean(form.app_id.trim() && form.secret_key.trim())
})

function providerName(provider: OCRProvider) {
  if (provider === "baidu") return "百度 OCR"
  return provider === "paddleocr" ? "PaddleOCR" : "MinerU"
}

function clearMessages() {
  errorMessage.value = ""
  successMessage.value = ""
}

async function load() {
  isLoading.value = true
  clearMessages()
  try {
    items.value = await getOCRKeys()
  } catch (error) {
    errorMessage.value = getErrorMessage(error)
  } finally {
    isLoading.value = false
  }
}

async function addKey() {
  if (!canSubmit.value) return
  isAdding.value = true
  clearMessages()
  try {
    const created = await createOCRKey({
      provider: form.provider,
      label: form.label.trim(),
      api_key: form.api_key.trim(),
      ...(form.provider === "baidu"
        ? { app_id: form.app_id.trim(), secret_key: form.secret_key.trim() }
        : {}),
      is_enabled: form.is_enabled,
    })
    items.value.push(created)
    form.label = ""
    form.app_id = ""
    form.api_key = ""
    form.secret_key = ""
    form.is_enabled = true
    successMessage.value = `${providerName(created.provider)} Key 已加密保存。`
  } catch (error) {
    errorMessage.value = getErrorMessage(error)
  } finally {
    isAdding.value = false
  }
}

async function toggleKey(item: OCRKeyItem) {
  if (busyId.value) return
  busyId.value = item.id
  clearMessages()
  try {
    const updated = await setOCRKeyEnabled(item.id, !item.is_enabled)
    items.value = items.value.map((current) => (current.id === item.id ? updated : current))
    successMessage.value = updated.is_enabled ? "Key 已开启，可参与随机调用。" : "Key 已关闭，不会再被随机选中。"
  } catch (error) {
    errorMessage.value = getErrorMessage(error)
  } finally {
    busyId.value = ""
  }
}

async function removeKey(item: OCRKeyItem) {
  if (busyId.value || !window.confirm(`确认删除这个 ${providerName(item.provider)} Key？`)) return
  busyId.value = item.id
  clearMessages()
  try {
    await deleteOCRKey(item.id)
    items.value = items.value.filter((current) => current.id !== item.id)
    successMessage.value = "Key 已删除。"
  } catch (error) {
    errorMessage.value = getErrorMessage(error)
  } finally {
    busyId.value = ""
  }
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section class="ocr-key-pool" aria-labelledby="ocr-key-pool-title">
    <div class="pool-heading">
      <div>
        <h2 id="ocr-key-pool-title">OCR 平台 Key 池</h2>
        <p>图片和扫描 PDF 将发送至所选第三方平台识别。每次仅从已开启 Key 中随机调用，失败后尝试其他 Key。</p>
      </div>
      <span class="enabled-summary">{{ enabledCount }} / {{ items.length }} 已开启</span>
    </div>

    <p v-if="errorMessage" class="pool-message pool-error" role="alert">{{ errorMessage }}</p>
    <p v-if="successMessage" class="pool-message pool-success" role="status">{{ successMessage }}</p>

    <form class="key-create-form" @submit.prevent="addKey">
      <label>
        <span>平台</span>
        <select v-model="form.provider" :disabled="isAdding">
          <option value="mineru">MinerU</option>
          <option value="paddleocr">PaddleOCR</option>
          <option value="baidu">百度 OCR（每月免费额度）</option>
        </select>
      </label>
      <label>
        <span>备注</span>
        <input v-model="form.label" type="text" maxlength="80" placeholder="例如：主账号" :disabled="isAdding" />
      </label>
      <label v-if="form.provider === 'baidu'" class="key-secret-field">
        <span>AppID</span>
        <input
          v-model="form.app_id"
          type="text"
          inputmode="numeric"
          autocomplete="off"
          placeholder="百度应用 AppID"
          :required="form.provider === 'baidu'"
          :disabled="isAdding"
        />
      </label>
      <label class="key-secret-field">
        <span>API Key</span>
        <input
          v-model="form.api_key"
          type="password"
          autocomplete="new-password"
          placeholder="保存后仅显示掩码"
          required
          :disabled="isAdding"
        />
      </label>
      <label v-if="form.provider === 'baidu'" class="key-secret-field">
        <span>Secret Key</span>
        <input
          v-model="form.secret_key"
          type="password"
          autocomplete="new-password"
          placeholder="仅加密保存，绝不回显"
          :required="form.provider === 'baidu'"
          :disabled="isAdding"
        />
      </label>
      <label class="key-enabled-field">
        <input v-model="form.is_enabled" type="checkbox" :disabled="isAdding" />
        <span>创建后立即开启</span>
      </label>
      <button class="add-key-button" type="submit" :disabled="!canSubmit">
        {{ isAdding ? "保存中..." : "添加 Key" }}
      </button>
    </form>

    <p v-if="isLoading" class="pool-empty">正在加载 Key 配置...</p>
    <p v-else-if="!items.length" class="pool-empty">尚未配置 OCR Key；未配置时图片仍使用视觉模型，扫描 PDF 无法识别。</p>

    <ul v-else class="key-list">
      <li v-for="item in items" :key="item.id" class="key-item" :class="{ disabled: !item.is_enabled }">
        <div class="key-main">
          <div class="key-title-line">
            <strong>{{ providerName(item.provider) }}</strong>
            <span v-if="item.label" class="key-label">{{ item.label }}</span>
            <span class="key-status" :class="{ on: item.is_enabled }">{{ item.is_enabled ? "已开启" : "已关闭" }}</span>
          </div>
          <code><template v-if="item.app_id">AppID {{ item.app_id}} · </template>{{ item.api_key_masked }}</code>
          <small>
            已调用 {{ item.use_count }} 次
            <template v-if="item.last_status === 'success'">；最近成功</template>
            <template v-else-if="item.last_status === 'failed'">；最近失败：{{ item.last_error }}</template>
          </small>
        </div>
        <div class="key-actions">
          <button
            class="toggle-key-button"
            :class="{ off: item.is_enabled }"
            type="button"
            :disabled="busyId === item.id"
            @click="toggleKey(item)"
          >
            {{ busyId === item.id ? "处理中..." : item.is_enabled ? "关闭" : "开启" }}
          </button>
          <button class="delete-key-button" type="button" :disabled="busyId === item.id" @click="removeKey(item)">
            删除
          </button>
        </div>
      </li>
    </ul>
  </section>
</template>

<style scoped src="./OCRKeyPool.css"></style>
