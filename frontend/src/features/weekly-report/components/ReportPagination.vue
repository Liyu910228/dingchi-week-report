<script setup lang="ts">
import PaginationBar from "@/components/navigation/PaginationBar.vue"
defineProps<{ page: number; pageSize: number; total: number; totalPages: number; disabled?: boolean }>()
defineEmits<{ change: [page: number] }>()
</script>
<template><PaginationBar v-bind="$props" @change="$emit('change', $event)" /></template>
