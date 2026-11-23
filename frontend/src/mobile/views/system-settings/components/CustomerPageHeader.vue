<script setup lang="ts">
defineProps<{
  total: number
  isLoading?: boolean
}>()

defineEmits<{
  create: []
}>()
</script>

<template>
  <section class="customer-hero">
    <div>
      <div class="customer-heading">
        <h2>客户列表</h2>
        <span v-if="!isLoading" class="customer-count">{{ total }} 个客户</span>
      </div>
    </div>
    <button class="primary-button" type="button" @click="$emit('create')">新增客户</button>
  </section>
</template>

<style scoped src="./CustomerPageHeader.css"></style>

