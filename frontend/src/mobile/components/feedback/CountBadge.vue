<script setup lang="ts">
defineProps<{count:number}>()
</script>
<template><span v-if="count>0" class="count-badge" :aria-label="`${count} 条待处理`">{{count>99?'99+':count}}</span></template>
<style scoped src="./CountBadge.css"></style>
