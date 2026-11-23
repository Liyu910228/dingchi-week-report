<script setup lang="ts">
const value=defineModel<string>({default:""})
defineProps<{readonly?:boolean;disabled?:boolean}>()
</script>
<template><section class="dashboard-card change-reason-panel"><label><span>变更原因</span><p class="user-content" v-if="readonly">{{value || '—'}}</p><textarea aria-label="变更原因" class="user-content" v-else v-model="value" rows="5" maxlength="10000" placeholder="请输入变更原因（非必填）" :disabled="disabled" /></label></section></template>
<style scoped src="./ChangeReasonPanel.css"></style>
