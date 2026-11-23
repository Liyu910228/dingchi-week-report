<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"
import type { TaskTemplateOption } from "@/mobile/features/weekly-report/task-editing"

const props = withDefaults(defineProps<{ open: boolean; anchor: HTMLElement | null; trigger: HTMLElement | null; selected: string; customerLabel?: string; templates?: readonly TaskTemplateOption[] }>(), { templates: () => [], customerLabel: "客户" })
const emit = defineEmits<{ close: []; select: [index: number] }>()
const panel = ref<HTMLElement | null>(null)
const style = ref<Record<string, string>>({})
let observer: ResizeObserver | undefined
function position() {
  if (!props.open || !props.anchor?.isConnected) return
  const rect = props.anchor.getBoundingClientRect()
  const available = window.innerWidth - rect.right - 12
  const adjacent = available >= 280
  const width = adjacent ? Math.min(440, available) : Math.min(440, rect.width, window.innerWidth - 24)
  const left = adjacent ? rect.right : Math.max(12, Math.min(rect.right - width, window.innerWidth - width - 12))
  const top = 12
  style.value = { left: `${left}px`, top: `${top}px`, width: `${width}px`, height: `${Math.max(0, window.innerHeight - 24)}px` }
}
function outside(event: PointerEvent) {
  if (!props.open || !(event.target instanceof Node)) return
  if (!panel.value?.contains(event.target) && !props.trigger?.contains(event.target)) emit("close")
}
watch(() => props.open, async open => {
  observer?.disconnect()
  if (!open) return
  await nextTick()
  if (!props.open || !props.anchor?.isConnected) return
  position()
  observer = new ResizeObserver(position)
  if (props.anchor) observer.observe(props.anchor)
  const input = panel.value?.querySelector<HTMLInputElement>("input:checked") || panel.value?.querySelector<HTMLInputElement>("input")
  input?.focus({ preventScroll: true })
})
onMounted(() => {
  window.addEventListener("resize", position)
  window.addEventListener("scroll", position, true)
  document.addEventListener("pointerdown", outside, true)
})
onBeforeUnmount(() => {
  observer?.disconnect()
  window.removeEventListener("resize", position)
  window.removeEventListener("scroll", position, true)
  document.removeEventListener("pointerdown", outside, true)
})
</script>
<template>
  <Teleport to="body">
    <section v-if="open" ref="panel" class="template-popover" :style="style" role="dialog" aria-label="选择任务模板" @keydown.esc.stop.prevent="emit('close')">
      <header class="popover-heading"><strong>选择任务模板</strong><button type="button" class="popover-close" aria-label="关闭模板列表" @click="emit('close')">×</button></header>
      <div class="popover-list" role="radiogroup" aria-label="工作任务模板">
        <label v-for="(item, index) in templates" :key="index" class="template-choice" :class="{ selected: selected === String(index) }" @click.prevent="emit('select', index)">
          <input type="radio" name="delivery-task-template" :value="index" :checked="selected === String(index)" @change="emit('select', index)" />
          <span class="choice-content"><span v-if="item.customer" class="choice-task"><span class="choice-label">{{ customerLabel }}</span><strong>{{ item.customer }}</strong></span><span v-if="item.dimension" class="choice-task"><span class="choice-label">维度</span><strong>{{ item.dimension }}</strong></span><span class="choice-task"><span class="choice-label">工作任务</span><strong>{{ item.task }}</strong></span><span class="choice-work"><span class="choice-label">主要工作内容</span><span>{{ item.work }}</span></span></span>
        </label>
      </div>
    </section>
  </Teleport>
</template>
<style scoped src="./TaskTemplatePopover.css"></style>
