<script setup lang="ts">
import { RouterLink, useRouter, type RouteLocationRaw } from "vue-router"

const props = defineProps<{
  to?: RouteLocationRaw
}>()
const router = useRouter()

function goBack() {
  router.back()
}
</script>

<template>
  <RouterLink
    v-if="props.to"
    class="back-button"
    :to="props.to"
    aria-label="返回"
    title="返回"
  >
    <span class="back-button__icon" aria-hidden="true" />
  </RouterLink>
  <button
    v-else
    class="back-button"
    type="button"
    aria-label="返回"
    title="返回"
    @click="goBack"
  >
    <span class="back-button__icon" aria-hidden="true" />
  </button>
</template>

<style scoped src="./BackButton.css"></style>
