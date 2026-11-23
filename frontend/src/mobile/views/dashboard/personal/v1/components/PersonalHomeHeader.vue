<script setup lang="ts">
import DashboardOverviewHeader from "@/mobile/components/layout/DashboardOverviewHeader.vue"
defineProps<{period:{start:string;end:string};roleName?:string;userName?:string}>()
defineEmits<{"update:start":[value:string]}>()
</script>
<template><DashboardOverviewHeader title="本周工作概览" :period="period" @update:start="$emit('update:start',$event)" /></template>
