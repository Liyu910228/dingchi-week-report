<script setup lang="ts">
import { ref } from "vue"
const expanded=ref(false)
</script>
<template>
 <section class="collapsible-filters" aria-label="筛选条件">
  <button class="filter-toggle" type="button" :aria-expanded="expanded" @click="expanded=!expanded">{{expanded?'收起筛选':'筛选'}}<span aria-hidden="true">{{expanded?'−':'+'}}</span></button>
  <div v-show="expanded" class="filter-body"><slot /></div>
 </section>
</template>
<style scoped src="./CollapsibleFilters.css"></style>
