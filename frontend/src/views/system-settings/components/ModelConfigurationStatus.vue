<script setup lang="ts">
import { computed } from "vue"

import type { ModelConfiguration, ModelConfigurationTestResult } from "@/features/ai-config/types"

const props = defineProps<{
  configuration: ModelConfiguration | null
  testResult: ModelConfigurationTestResult | null
}>()

const sourceLabel = computed(() => {
  if (!props.configuration) return "--"
  return props.configuration.source === "database" ? "数据库配置" : "环境变量"
})

const testStatus = computed(() => {
  if (props.testResult) return props.testResult.success ? "成功" : "失败"
  const status = props.configuration?.last_test_status
  if (!status) return "尚未测试"
  if (status === "success") return "成功"
  if (status === "failed" || status === "failure") return "失败"
  return status
})

const testMessage = computed(() =>
  props.testResult?.message || props.configuration?.last_test_message || "暂无测试结果",
)

function formatTime(value: string | null | undefined) {
  if (!value) return "--"
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString("zh-CN")
}
</script>

<template>
  <section class="configuration-status" aria-label="配置状态">
    <div class="status-section">
      <h2>当前配置</h2>
      <dl class="status-grid">
        <div>
          <dt>配置来源</dt>
          <dd>{{ sourceLabel }}</dd>
        </div>
        <div>
          <dt>最近更新</dt>
          <dd>{{ formatTime(configuration?.updated_at) }}</dd>
        </div>
      </dl>
    </div>

    <div class="status-section">
      <h2>最近测试结果</h2>
      <dl class="status-grid">
        <div>
          <dt>状态</dt>
          <dd :class="{ 'test-failed': testStatus === '失败' }">{{ testStatus }}</dd>
        </div>
        <div>
          <dt>测试时间</dt>
          <dd>{{ testResult ? "刚刚" : formatTime(configuration?.last_tested_at) }}</dd>
        </div>
        <div v-if="testResult">
          <dt>模型 / 耗时</dt>
          <dd>{{ testResult.model || "--" }} / {{ testResult.latency_ms }} ms</dd>
        </div>
      </dl>
      <p class="test-message">{{ testMessage }}</p>
      <p v-if="testResult?.reply" class="test-reply">模型回复：{{ testResult.reply }}</p>
    </div>
  </section>
</template>

<style scoped src="./ModelConfigurationStatus.css"></style>
