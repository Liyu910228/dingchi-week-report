<script setup lang="ts">
withDefaults(
  defineProps<{
    text: string
    count?: number
  }>(),
  {
    count: 240,
  },
)
</script>

<template>
  <Teleport to="body">
    <div v-if="text" class="global-watermark" aria-hidden="true">
      <span v-for="index in count" :key="index">{{ text }}</span>
    </div>
  </Teleport>
</template>

<style scoped src="./GlobalWatermark.css"></style>
