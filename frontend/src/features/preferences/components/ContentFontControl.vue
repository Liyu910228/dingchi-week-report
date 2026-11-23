<script setup lang="ts">
import {useContentTypography,minimumContentFontSize,maximumContentFontSize,defaultContentFontSize} from "../useContentTypography"
const typography=useContentTypography()
</script>
<template>
 <section class="content-font-control" aria-label="用户填写内容字号">
  <div class="content-font-heading"><span>内容字号</span><output aria-live="polite">{{typography.size}}px</output><button type="button" :disabled="typography.size===defaultContentFontSize" @click="typography.reset">恢复默认</button></div>
  <div class="content-font-slider"><button type="button" aria-label="减小内容字号" :disabled="typography.size<=minimumContentFontSize" @click="typography.setSize(typography.size-1)">−</button><input type="range" aria-label="调整用户填写内容字号" :min="minimumContentFontSize" :max="maximumContentFontSize" step="1" :value="typography.size" @input="typography.setSize(Number(($event.target as HTMLInputElement).value))" /><button type="button" aria-label="增大内容字号" :disabled="typography.size>=maximumContentFontSize" @click="typography.setSize(typography.size+1)">＋</button></div>
 </section>
</template>
<style scoped src="./ContentFontControl.css"></style>
