<script setup lang="ts">
import {computed,onMounted,ref,watch} from "vue"
import SearchableSelect from "@/mobile/components/form/SearchableSelect.vue"
import {listDictionaryItems,type DictionaryItem} from "@/mobile/features/dictionary"
const props=defineProps<{roles:{role_code:string;role_name:string;customer_ids?:string[]}[];roleCodes:string[];disabled?:boolean}>()
const model=defineModel<Record<string,string[]>>({default:()=>({})})
const items=ref<DictionaryItem[]>([]),error=ref(""),loaded=ref(false)
const knownNames=new Map<string,string>()
const available=computed(()=>props.roles.filter(role=>props.roleCodes.includes(role.role_code)).flatMap(role=>items.value.filter(item=>role.customer_ids?.includes(item.id)).map(item=>({value:`${role.role_code}:${item.id}`,label:item.dict_name,description:role.role_name,group:role.role_name}))))
const selected=computed(()=>Object.entries(model.value).flatMap(([role,ids])=>ids.map(id=>`${role}:${id}`)))
const unavailable=computed(()=>selected.value.filter(value=>!available.value.some(item=>item.value===value)))
// 配置刷新不能隐式移除已选客户；不可选项保留显示，交由用户明确移除。
const options=computed(()=>[
 ...available.value,
 ...unavailable.value.map(value=>{
  const [code,id]=value.split(":");const role=props.roles.find(item=>item.role_code===code)
  return {value,label:knownNames.get(id || "") || `客户 ${id}`,description:`${role?.role_name || code} · 当前不可选`,group:role?.role_name || code,disabled:true}
 }),
])
function update(value:string|string[]){
 const next:Record<string,string[]>={}
 for(const item of Array.isArray(value)?value:[]){const [role,id]=item.split(":");if(role && id)(next[role] ||= []).push(id)}
 model.value=next
}
watch(()=>[...props.roleCodes],(codes,previous)=>{
 if(props.disabled)return
 const removed=previous.filter(code=>!codes.includes(code))
 if(!removed.length)return
 const next=Object.fromEntries(Object.entries(model.value).filter(([code])=>!removed.includes(code)))
 if(Object.keys(next).length!==Object.keys(model.value).length)model.value=next
})
async function load(){
 error.value=""
 try{const data=(await listDictionaryItems("customer")).items;for(const item of data)knownNames.set(item.id,item.dict_name);items.value=data;loaded.value=true}
 catch(cause){error.value=cause instanceof Error?cause.message:"客户加载失败。"}
}
onMounted(()=>void load())
</script>
<template>
 <div class="customer-selection">
  <SearchableSelect :model-value="selected" :options="options" multiple teleport-menu placeholder="无" aria-label="负责的客户" :disabled="disabled || !loaded" @update:model-value="update" />
  <p v-if="loaded && unavailable.length" role="status">部分已选客户当前不可选，请确认客户及职位配置后重新选择或移除。</p>
  <p v-if="error" role="alert">{{error}} <button type="button" @click="load">重试</button></p>
 </div>
</template>
<style scoped src="./UserCustomerAssignments.css"></style>

