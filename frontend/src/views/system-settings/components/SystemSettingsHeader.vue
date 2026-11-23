<script setup lang="ts">
import { RouterLink } from "vue-router"
</script>

<template>
  <section class="settings-header">
    <h1>系统设置</h1>
    <nav class="settings-tabs" aria-label="系统设置标签页">
      <RouterLink :to="{ name: 'system-settings-customers' }" active-class="is-active">
        客户管理
      </RouterLink>
      <RouterLink :to="{ name: 'system-settings-models' }" active-class="is-active">
        模型配置
      </RouterLink>
    </nav>
  </section>
</template>

<style scoped src="./SystemSettingsHeader.css"></style>
