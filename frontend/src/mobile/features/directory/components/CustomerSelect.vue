<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import SearchableSelect from "@/mobile/components/form/SearchableSelect.vue"
import { listDictionaryItems, type DictionaryItem } from "@/mobile/features/dictionary"
const props=defineProps<{showSelectAll?:boolean;modelValue?:string[];disabled?:boolean;allowedIds?:string[]}>()
const emit=defineEmits<{"update:modelValue":[value:string[]]}>()
const items=ref<DictionaryItem[]>([]),error=ref(""),loading=ref(false)
const options=computed(()=>items.value.filter(item=>!props.allowedIds || props.allowedIds.includes(item.id)).map(item=>({value:item.id,label:item.dict_name,description:item.dict_code})))
async function load(){loading.value=true;error.value="";try{items.value=(await listDictionaryItems("customer")).items}catch(cause){error.value=cause instanceof Error?cause.message:"客户加载失败。"}finally{loading.value=false}}
onMounted(()=>void load())
</script>
<template><div class="customer-selection"><SearchableSelect :model-value="modelValue || []" :options="options" :show-select-all="showSelectAll" multiple teleport-menu placeholder="无" aria-label="负责的客户" :disabled="disabled || loading" @update:model-value="emit('update:modelValue',Array.isArray($event)?$event:[])" /><p v-if="error" role="alert">{{error}} <button type="button" @click="load">重试</button></p></div></template>
<style scoped src="./CustomerSelect.css"></style>

