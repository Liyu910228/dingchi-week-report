<script setup lang="ts">
import { watch } from "vue"

import { useNoticeStore } from "@/app/stores/notice"

const props = withDefaults(
  defineProps<{
    warningMessage?: string
    reminderMessage?: string
  }>(),
  { warningMessage: "", reminderMessage: "" },
)

const noticeStore = useNoticeStore()

watch(
  () => props.warningMessage,
  (message) => {
    if (message) noticeStore.warning(message)
  },
  { immediate: true },
)

watch(
  () => props.reminderMessage,
  (message) => {
    if (message) noticeStore.reminder(message)
  },
  { immediate: true },
)
</script>

<template>
  <span class="notice-bridge" aria-hidden="true"></span>
</template>

<style scoped>
.notice-bridge {
  display: none;
}
</style>
