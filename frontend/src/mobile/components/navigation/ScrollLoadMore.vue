<script setup lang="ts">
import InfiniteListFooter from "./InfiniteListFooter.vue"
const props=withDefaults(defineProps<{showEnd?:boolean;page:number;pageSize:number;total:number;totalPages:number;disabled?:boolean;error?:string}>(),{showEnd:true})
const emit=defineEmits<{change:[page:number]}>()
function more(){if(!props.disabled && props.page<props.totalPages)emit('change',props.page+1)}
</script>
<template><InfiniteListFooter :loading="Boolean(disabled)" :has-more="page<totalPages" :error="error || ''" :page="page" :total="total" :show-end="showEnd" @more="more" /></template>



