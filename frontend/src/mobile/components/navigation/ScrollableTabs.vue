<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"
import { ChevronLeft, ChevronRight } from "lucide-vue-next"
const props = defineProps<{ items: { id: string; name: string }[]; modelValue: string; ariaLabel?:string; tabIdPrefix?:string; panelId?:string }>()
const emit = defineEmits<{ "update:modelValue": [value: string] }>()
const track = ref<HTMLElement | null>(null)
const overflow = ref(false)
const atStart = ref(true)
const atEnd = ref(false)
let observer: ResizeObserver | undefined
function measure() {
  const el = track.value
  if (!el) return
  overflow.value = el.scrollWidth > el.clientWidth + 1
  atStart.value = el.scrollLeft <= 1
  atEnd.value = el.scrollLeft + el.clientWidth >= el.scrollWidth - 1
}
function scroll(direction: number) {
  track.value?.scrollBy({ left: direction * Math.max(120, track.value.clientWidth * 0.7), behavior: "smooth" })
}
async function revealSelected() {
  await nextTick()
  measure()
  const el = track.value
  const selected = el?.querySelector<HTMLElement>('[aria-selected="true"]')
  if (el && selected) {
    if (selected.offsetLeft < el.scrollLeft) el.scrollLeft = selected.offsetLeft
    else if (selected.offsetLeft + selected.offsetWidth > el.scrollLeft + el.clientWidth)
      el.scrollLeft = selected.offsetLeft + selected.offsetWidth - el.clientWidth
  }
}
onMounted(() => {
  observer = new ResizeObserver(measure)
  if (track.value) observer.observe(track.value)
  void revealSelected()
})
watch(() => [props.items, props.modelValue], revealSelected, { deep: true })
onBeforeUnmount(() => observer?.disconnect())
</script>

<template>
  <div class="scrollable-tabs">
    <button v-if="overflow" class="tab-arrow" type="button" aria-label="向左滚动标签" :disabled="atStart" @click="scroll(-1)"><ChevronLeft :size="18" /></button>
    <div ref="track" class="tab-track" role="tablist" :aria-label="ariaLabel || '标签切换'" @scroll="measure">
      <button v-for="item in items" :key="item.id" :id="tabIdPrefix ? `${tabIdPrefix}${item.id}` : undefined" :aria-controls="panelId" type="button" role="tab" :aria-selected="modelValue === item.id"
        :class="{ active: modelValue === item.id }" @click="emit('update:modelValue', item.id)">{{ item.name }}<slot name="suffix" :item="item" /></button>
    </div>
    <button v-if="overflow" class="tab-arrow" type="button" aria-label="向右滚动标签" :disabled="atEnd" @click="scroll(1)"><ChevronRight :size="18" /></button>
  </div>
</template>
<style scoped src="./ScrollableTabs.css"></style>
