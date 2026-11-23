<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue"
import { Maximize2, X } from "lucide-vue-next"

defineOptions({ inheritAttrs: false })
defineProps<{ title: string }>()
const isFullscreen = ref(false)
let previousOverflow = ""
function restorePage() {
  document.documentElement.style.overflow = previousOverflow
}
watch(isFullscreen, (expanded) => {
  if (expanded) {
    previousOverflow = document.documentElement.style.overflow
    document.documentElement.style.overflow = "hidden"
  } else restorePage()
}, { flush: "sync" })
onBeforeUnmount(() => { if (isFullscreen.value) restorePage() })
</script>

<template>
  <Teleport to="body" :disabled="!isFullscreen">
    <section v-bind="$attrs" class="fullscreen-panel" :class="{ 'fullscreen-panel--expanded': isFullscreen }">
      <header class="fullscreen-panel__header">
        <h2>{{ title }}</h2>
      </header>
      <div class="fullscreen-panel__toolbar">
        <slot name="tabs" />
        <div class="fullscreen-panel__actions">
          <slot name="actions" />
          <button class="fullscreen-panel__toggle" type="button"
            :aria-label="isFullscreen ? '退出全屏' : '全屏显示'"
            :title="isFullscreen ? '退出全屏' : '全屏显示'" :aria-pressed="isFullscreen"
            @click="isFullscreen = !isFullscreen">
            <component :is="isFullscreen ? X : Maximize2" :size="20" aria-hidden="true" />
          </button>
        </div>
      </div>
      <div class="fullscreen-panel__body"><slot /></div>
    </section>
  </Teleport>
</template>

<style scoped src="./FullscreenPanel.css"></style>
