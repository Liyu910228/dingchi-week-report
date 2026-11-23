<script setup lang="ts">
import { computed, provide } from "vue"
import { taskPreviewLimitKey } from "@/mobile/shared/task-preview"
const props=defineProps<{limit:number}>()
provide(taskPreviewLimitKey,computed(()=>props.limit))
</script>
<template><slot /></template>
