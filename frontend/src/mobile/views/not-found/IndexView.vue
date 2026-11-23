<script setup lang="ts">
import { RouterLink } from "vue-router"
</script>

<template>
  <section class="not-found surface-card">
    <span class="eyebrow">404</span>
    <h1>这个页面还没有被创建</h1>
    <p>地址可能有误，或对应功能仍在开发中。</p>
    <RouterLink class="primary-button" to="/mobile">返回工作台</RouterLink>
  </section>
</template>

<style scoped src="./IndexView.css"></style>
