<script setup lang="ts">
import SubmissionForm from "@/mobile/features/submissions/components/SubmissionForm.vue"
</script>
<template><SubmissionForm kind="monthly" readonly :key="$route.fullPath" /></template>
