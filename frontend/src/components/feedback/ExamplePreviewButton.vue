<script setup lang="ts">
import { onBeforeUnmount, ref, useId } from "vue"

import { useExamplePreviewPosition } from "./useExamplePreviewPosition"

export interface ExamplePreviewField {
  label: string
  value?: string
  rows?: ReadonlyArray<ExamplePreviewRow>
}

export interface ExamplePreviewRow {
  label: string
  value: string
}

withDefaults(
  defineProps<{
    content: string
    label?: string
    panelTitle?: string
    fields?: ReadonlyArray<ExamplePreviewField>
  }>(),
  {
    label: "填写样例",
    panelTitle: "填写样例",
  },
)

const isOpen = ref(false)
const trigger = ref<HTMLButtonElement | null>(null)
const panel = ref<HTMLDivElement | null>(null)
const panelId = useId()
const { position, isPositioned } = useExamplePreviewPosition(isOpen, trigger, panel)
let closeTimer: ReturnType<typeof setTimeout> | undefined

function openPreview() {
  clearTimeout(closeTimer)
  isOpen.value = true
}

function scheduleClose() {
  clearTimeout(closeTimer)
  closeTimer = setTimeout(() => {
    const focused = document.activeElement
    if (focused === trigger.value || panel.value?.contains(focused)) return
    isOpen.value = false
  }, 200)
}

function closePreview() {
  clearTimeout(closeTimer)
  isOpen.value = false
}

onBeforeUnmount(() => clearTimeout(closeTimer))
</script>

<template>
  <div class="example-preview" @mouseenter="openPreview" @mouseleave="scheduleClose">
    <button
      ref="trigger"
      class="example-preview__trigger"
      type="button"
      :aria-label="`${label}（悬浮查看）`"
      :aria-expanded="isOpen"
      :aria-controls="panelId"
      @click="openPreview"
      @focus="openPreview"
      @blur="scheduleClose"
      @keydown.esc="closePreview"
    >
      {{ label }}
    </button>
  </div>
  <Teleport to="body">
    <div
      v-if="isOpen"
      :id="panelId"
      ref="panel"
      class="example-preview__panel"
      role="tooltip"
      tabindex="-1"
      :style="[position, { visibility: isPositioned ? 'visible' : 'hidden' }]"
      @mouseenter="openPreview"
      @mouseleave="scheduleClose"
      @focusin="openPreview"
      @focusout="scheduleClose"
      @keydown.esc="closePreview"
    >
      <div class="example-preview__panel-header">
        <strong>{{ panelTitle }}</strong>
      </div>
      <div class="example-preview__scroll">
        <div v-if="fields?.length" class="example-preview__fields">
          <div v-for="field in fields" :key="field.label" class="example-preview__field">
            <span class="example-preview__field-label">{{ field.label }}</span>
            <div v-if="field.rows?.length" class="example-preview__field-rows">
              <div v-for="row in field.rows" :key="row.label" class="example-preview__field-row">
                <span class="example-preview__field-row-label">{{ row.label }}</span>
                <div class="example-preview__field-row-value">{{ row.value }}</div>
              </div>
            </div>
            <div v-else class="example-preview__field-value">{{ field.value }}</div>
          </div>
        </div>
        <pre v-else class="example-preview__content">{{ content }}</pre>
      </div>
    </div>
  </Teleport>
</template>

<style scoped src="./ExamplePreviewButton.css"></style>
