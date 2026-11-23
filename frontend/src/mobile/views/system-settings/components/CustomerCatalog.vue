<script setup lang="ts">
import { computed, ref, watch } from "vue"
import ScrollLoadMore from "@/mobile/components/navigation/ScrollLoadMore.vue"
import type { Customer } from "@/mobile/features/dictionary"
const props=defineProps<{customers:Customer[];isLoading?:boolean}>()
defineEmits<{edit:[customer:Customer];delete:[customer:Customer]}>()
const page=ref(1),pageSize=10
const totalPages=computed(()=>Math.max(1,Math.ceil(props.customers.length/pageSize)))
const visible=computed(()=>props.customers.slice(0,page.value*pageSize))
watch(totalPages,value=>{page.value=Math.min(page.value,value)})
</script>
<template>
 <div class="customer-catalog">
  <p v-if="isLoading && !customers.length" class="empty-card" role="status">正在加载客户数据…</p>
  <p v-else-if="!customers.length" class="empty-card">暂无客户数据</p>
  <div v-else class="customer-cards">
   <article v-for="customer in visible" :key="customer.id" class="customer-card">
    <div class="customer-card-heading"><h3>{{customer.dict_name}}</h3><span class="customer-status" :class="{'is-active':customer.status==='active'}">{{customer.status==='active'?'启用':'停用'}}</span></div>
    <dl class="customer-fields"><div><dt>客户编号</dt><dd>{{customer.dict_code}}</dd></div><div><dt>排序</dt><dd>{{customer.sort_order}}</dd></div></dl>
    <div class="customer-actions"><button type="button" @click="$emit('edit',customer)">编辑</button><button class="is-danger" type="button" @click="$emit('delete',customer)">删除</button></div>
   </article>
  </div>
  <ScrollLoadMore :page="page" :page-size="pageSize" :total="customers.length" :total-pages="totalPages" :disabled="isLoading" @change="page=$event" />
 </div>
</template>
<style scoped src="./CustomerCatalog.css"></style>
