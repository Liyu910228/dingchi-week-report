<script setup lang="ts">
import { ref, useId } from "vue"

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
function openPreview() { isOpen.value = true }
function closePreview() { isOpen.value = false }
</script>

<template>
  <div class="example-preview">
    <button
      ref="trigger"
      class="example-preview__trigger"
      type="button"
      :aria-label="label"
      aria-haspopup="dialog"
      :aria-expanded="isOpen"
      :aria-controls="panelId"
      @click="openPreview"
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
      role="dialog"
      :aria-label="panelTitle"
      tabindex="-1"
      :style="[position, { visibility: isPositioned ? 'visible' : 'hidden' }]"
     
     
      @keydown.esc="closePreview"
    >
      <div class="example-preview__panel-header">
        <strong>{{ panelTitle }}</strong>
        <button class="example-preview__close" type="button" aria-label="关闭填写样例" @click.stop="closePreview">关闭</button>
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
