<script setup lang="ts">
import SubmissionForm from "@/features/submissions/components/SubmissionForm.vue"
</script>
<template><SubmissionForm kind="weekly" readonly :key="$route.fullPath" /></template>
