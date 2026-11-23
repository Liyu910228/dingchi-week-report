<script setup lang="ts">
import SubmissionForm from "@/features/submissions/components/SubmissionForm.vue"
</script>
<template><SubmissionForm kind="monthly" readonly :key="$route.fullPath" /></template>
