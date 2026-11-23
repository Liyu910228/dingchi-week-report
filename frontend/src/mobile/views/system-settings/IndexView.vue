<script setup lang="ts">
import { RouterView } from "vue-router"

import SystemSettingsHeader from "./components/SystemSettingsHeader.vue"
</script>

<template>
  <div class="settings-page">
    <SystemSettingsHeader />
    <RouterView />
  </div>
</template>

<style scoped src="./IndexView.css"></style>
