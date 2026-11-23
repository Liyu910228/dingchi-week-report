<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    open: boolean
    title: string
    description?: string
    busy?: boolean
    width?: string
    height?: string
    fullscreen?: boolean
    overflowVisible?: boolean
  }>(),
  {
    description: "",
    busy: false,
    width: "640px",
    height: "",
    fullscreen: false,
    overflowVisible: false,
  },
)

const emit = defineEmits<{
  close: []
}>()

function requestClose() {
  if (!props.busy) emit("close")
}

</script>

<template>
  <Teleport to="body">
    <Transition name="base-dialog">
      <div v-if="open" class="dialog-backdrop">
        <section
          aria-modal="true"
          class="dialog-panel"
          :class="{
            'dialog-panel--fixed': Boolean(height) || fullscreen,
            'dialog-panel--fullscreen': fullscreen,
            'dialog-panel--overflow-visible': overflowVisible,
          }"
          role="dialog"
          :aria-label="title"
          :style="{ '--dialog-width': width, '--dialog-height': height || undefined }"
        >
          <header class="dialog-header">
            <div>
              <h2>{{ title }}</h2>
              <p v-if="description">{{ description }}</p>
            </div>
            <button
              aria-label="关闭弹窗"
              class="dialog-close"
              type="button"
              :disabled="busy"
              @click="requestClose"
            >
              ×
            </button>
          </header>
          <div class="dialog-body">
            <slot />
          </div>
          <footer v-if="$slots.actions" class="dialog-actions">
            <slot name="actions" />
          </footer>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped src="./BaseDialog.css"></style>
