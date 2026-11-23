<script setup lang="ts">
import { Plus } from "lucide-vue-next"
defineEmits<{add:[]}>()
</script>
<template><div class="task-add-footer"><button class="ghost-button" type="button" @click="$emit('add')"><Plus :size="18" aria-hidden="true" /><span>新增任务</span></button></div></template>
<style scoped src="./TaskAddFooter.css"></style>
