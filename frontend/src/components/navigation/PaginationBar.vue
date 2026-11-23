<script setup lang="ts">
import { computed } from "vue"

const props = defineProps<{
  page: number
  pageSize: number
  total: number
  totalPages: number
  disabled?: boolean
}>()

const emit = defineEmits<{ change: [page: number] }>()

const visiblePages = computed(() => {
  if (!props.totalPages) return []
  const start = Math.max(1, Math.min(props.page - 2, props.totalPages - 4))
  const end = Math.min(props.totalPages, start + 4)
  return Array.from({ length: end - start + 1 }, (_, index) => start + index)
})
</script>

<template>
  <div v-if="total" class="report-pagination">
    <span>共 {{ total }} 条</span>
    <div class="pagination-buttons">
      <button
        class="pagination-button"
        type="button"
        :disabled="disabled || page <= 1"
        @click="emit('change', page - 1)"
      >
        上一页
      </button>
      <button
        v-for="item in visiblePages"
        :key="item"
        class="pagination-button"
        :class="{ 'is-active': item === page }"
        type="button"
        :disabled="disabled"
        @click="emit('change', item)"
      >
        {{ item }}
      </button>
      <button
        class="pagination-button"
        type="button"
        :disabled="disabled || page >= totalPages"
        @click="emit('change', page + 1)"
      >
        下一页
      </button>
    </div>
    <span>每页 {{ pageSize }} 条</span>
  </div>
</template>

<style scoped src="./PaginationBar.css"></style>
