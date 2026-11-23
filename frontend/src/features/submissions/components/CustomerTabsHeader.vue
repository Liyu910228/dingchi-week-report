<script setup lang="ts">
import {inject} from "vue"
import ScrollableTabs from "@/components/navigation/ScrollableTabs.vue"
import {customerScopeKey} from "../customer-scope"
const scope=inject(customerScopeKey,undefined)
</script>
<template><ScrollableTabs v-if="scope?.enabled.value" :model-value="scope.active.value" :items="scope.tabs.value" @update:model-value="scope.active.value=$event" /></template>
