<script setup lang="ts">
import { defineAsyncComponent } from "vue"
import { useRoute, RouterView } from "vue-router"

import DefaultLayout from "@/layouts/DefaultLayout.vue"
const MobileLayout = defineAsyncComponent(() => import("@/mobile/layouts/DefaultLayout.vue"))
const route = useRoute()
</script>

<template>
  <component :is="route.path === '/mobile' || route.path.startsWith('/mobile/') ? MobileLayout : DefaultLayout">
    <RouterView />
  </component>
</template>
