<script setup lang="ts">
import { reactive } from "vue"
import { useLegacyDashboard } from "./composables/useLegacyDashboard"
import LegacyDashboardContent from "./components/LegacyDashboardContent.vue"

const state = reactive(useLegacyDashboard())
</script>

<template>
  <LegacyDashboardContent :state="state" />
</template>