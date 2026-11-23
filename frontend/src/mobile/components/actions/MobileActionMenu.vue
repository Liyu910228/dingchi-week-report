<script setup lang="ts">
import { ref } from "vue"
defineProps<{fullscreen?:boolean}>()
const open=ref(false)
defineEmits<{fullscreen:[]}>()
function dismiss(event:MouseEvent){if((event.target as HTMLElement).closest('button'))open.value=false}
</script>
<template>
 <button class="more-trigger" type="button" :aria-expanded="open" @click="open=true">更多</button>
 <Teleport to="body"><div v-show="open" class="action-menu-backdrop" @click.self="open=false" @keydown.esc="open=false">
  <section class="action-menu-panel" role="dialog" aria-label="更多操作"><header><h3>更多操作</h3><button type="button" @click="open=false">关闭</button></header><div class="action-menu-items" @click="dismiss"><slot /><button type="button" @click="$emit('fullscreen')">{{fullscreen ? '退出全屏' : '全屏查看'}}</button></div></section>
 </div></Teleport>
</template>
<style scoped src="./MobileActionMenu.css"></style>
