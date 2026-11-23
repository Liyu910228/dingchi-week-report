<script setup lang="ts">
import { onMounted } from "vue"

import NoticeBridge from "@/components/feedback/NoticeBridge.vue"

import ModelConfigurationForm from "./components/ModelConfigurationForm.vue"
import ModelConfigurationStatus from "./components/ModelConfigurationStatus.vue"
import OCRKeyPool from "./components/OCRKeyPool.vue"
import { useModelConfiguration } from "./composables/useModelConfiguration"

const modelConfiguration = useModelConfiguration()

onMounted(() => {
  void modelConfiguration.load()
})
</script>

<template>
  <div class="model-configuration-page">
    <NoticeBridge
      :warning-message="modelConfiguration.errorMessage.value"
      :reminder-message="modelConfiguration.successMessage.value"
    />
    <ModelConfigurationForm
      :form="modelConfiguration.form"
      :has-api-key="modelConfiguration.configuration.value?.has_api_key ?? false"
      :api-key-masked="modelConfiguration.configuration.value?.api_key_masked ?? ''"
      :is-loading="modelConfiguration.isLoading.value"
      :is-saving="modelConfiguration.isSaving.value"
      :is-testing="modelConfiguration.isTesting.value"
      :is-busy="modelConfiguration.isBusy.value"
      @save="modelConfiguration.save"
      @test="modelConfiguration.test"
    />
    <ModelConfigurationStatus
      :configuration="modelConfiguration.configuration.value"
      :test-result="modelConfiguration.testResult.value"
    />
    <OCRKeyPool />
  </div>
</template>

<style scoped src="./ModelConfigurationView.css"></style>
