<script setup lang="ts">
defineProps<{
  name: "home" | "report" | "users" | "roles" | "sparkles" | "settings"
}>()
</script>

<template>
  <svg class="nav-symbol" viewBox="0 0 24 24" aria-hidden="true">
    <template v-if="name === 'home'">
      <path d="M3.8 10.4 12 3.8l8.2 6.6" />
      <path d="M5.7 9.5v10.1h12.6V9.5M9.4 19.6v-6.2h5.2v6.2" />
    </template>

    <template v-else-if="name === 'report'">
      <rect x="5" y="3.5" width="14" height="17" rx="2.3" />
      <path d="M8.2 8.1h7.6M8.2 12h4.8M8.2 15.9h7.6" />
      <path d="m14.6 11.9 1.1 1.1 2-2.2" />
    </template>

    <template v-else-if="name === 'users'">
      <circle cx="9" cy="8.1" r="3.1" />
      <path d="M3.8 19.6v-1.2A5.2 5.2 0 0 1 9 13.2a5.2 5.2 0 0 1 5.2 5.2v1.2" />
      <path d="M14.5 5.6a3 3 0 0 1 0 5.6M15.8 13.5a5 5 0 0 1 4.4 5v1.1" />
    </template>

    <template v-else-if="name === 'roles'">
      <path d="M12 3.2 19 6v5.1c0 4.4-2.8 7.7-7 9.7-4.2-2-7-5.3-7-9.7V6z" />
      <circle cx="12" cy="9.2" r="2.2" />
      <path d="M8.6 16a3.4 3.4 0 0 1 6.8 0" />
    </template>

    <template v-else-if="name === 'settings'">
      <circle cx="12" cy="12" r="3" />
      <path d="M12 3.2v2.4M12 18.4v2.4M3.2 12h2.4M18.4 12h2.4M5.6 5.6l1.7 1.7M16.7 16.7l1.7 1.7M5.6 18.4l1.7-1.7M16.7 7.3l1.7-1.7" />
    </template>

    <template v-else>
      <path d="m12 3 .8 2.7A4.8 4.8 0 0 0 16 8.9l2.7.8-2.7.8a4.8 4.8 0 0 0-3.2 3.2L12 16.4l-.8-2.7A4.8 4.8 0 0 0 8 10.5l-2.7-.8L8 8.9a4.8 4.8 0 0 0 3.2-3.2z" />
      <path d="m18.5 15 .4 1.3a2.4 2.4 0 0 0 1.5 1.5l1.3.4-1.3.4a2.4 2.4 0 0 0-1.5 1.5l-.4 1.3-.4-1.3a2.4 2.4 0 0 0-1.5-1.5l-1.3-.4 1.3-.4a2.4 2.4 0 0 0 1.5-1.5z" />
    </template>
  </svg>
</template>

<style scoped>
.nav-symbol {
  display: block;
  width: 28px;
  height: 28px;
  overflow: visible;
  fill: none;
  stroke: currentColor;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 1.65;
}
</style>
