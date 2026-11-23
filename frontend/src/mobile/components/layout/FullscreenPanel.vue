<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue"
import MobileActionMenu from "@/mobile/components/actions/MobileActionMenu.vue"
import { X } from "lucide-vue-next"

defineOptions({ inheritAttrs: false })
defineProps<{ title: string; headerControls?: boolean }>()
const isFullscreen = ref(false)
let previousOverflow = ""
function restorePage() {
  document.documentElement.style.overflow = previousOverflow
}
watch(isFullscreen, (expanded) => {
  if (expanded) {
    previousOverflow = document.documentElement.style.overflow
    document.documentElement.style.overflow = "hidden"
  } else { restorePage() }
}, { flush: "sync" })
onBeforeUnmount(() => { if (isFullscreen.value) restorePage() })
</script>

<template>
  <Teleport to="body" :disabled="!isFullscreen">
    <section v-bind="$attrs" class="fullscreen-panel" :class="{ 'fullscreen-panel--expanded': isFullscreen, 'fullscreen-panel--header-controls': headerControls }">
      <header class="fullscreen-panel__header">
        <h2>{{title}}</h2>
        <div class="fullscreen-panel__heading-actions"><slot name="primary" />
          <MobileActionMenu :fullscreen="isFullscreen" @fullscreen="isFullscreen=!isFullscreen"><slot name="header-actions" /><slot name="actions" /></MobileActionMenu>
        </div>
      </header>
      <div v-if="$slots.tabs" class="fullscreen-panel__toolbar"><slot name="tabs" /></div>
      <div class="fullscreen-panel__body"><slot /></div>
    </section>
    <button v-if="isFullscreen" class="fullscreen-panel__close" type="button" aria-label="退出全屏" @click="isFullscreen = false"><X :size="20" aria-hidden="true" /></button>
  </Teleport>
</template>

<style scoped src="./FullscreenPanel.css"></style>
