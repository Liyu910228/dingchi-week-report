<script setup lang="ts" generic="T extends {customer_id?:string|null;customer_name?:string;customer_name_snapshot?:string;scope_name?:string}">
import {computed,onMounted,provide,ref,watch} from "vue"
import {listDictionaryItems,type DictionaryItem} from "@/mobile/features/dictionary"
import {customerScopeKey} from "../customer-scope"
import type {AssignedCustomer} from "../types"
const props=defineProps<{tasks:T[];customers:AssignedCustomer[];nameField?:"customer_name"|"customer_name_snapshot"|"scope_name"}>()
const emit=defineEmits<{"update:tasks":[tasks:T[]]}>()
const error=ref("")
const active=ref(props.customers[0]?.id || ""),all=ref<DictionaryItem[]>([])
const lookup=computed(()=>new Map([...all.value.map(item=>[item.id,item.dict_name] as const),...props.customers.map(item=>[item.id,item.name] as const)]))
function customerId(task:T){if(task.customer_id)return task.customer_id;const name=props.nameField?task[props.nameField]:"";return [...lookup.value].find(([,label])=>label===name)?.[0] || ""}
const tabs=computed(()=>{const items=new Map(props.customers.map(item=>[item.id,item.name]));for(const task of props.tasks){const id=customerId(task);items.set(id,lookup.value.get(id) || (id?`客户 ${id}`:"未分配客户"))}return [...items].map(([id,name])=>({id,name}))})
watch(tabs,items=>{if(!items.some(item=>item.id===active.value))active.value=items[0]?.id || ""})
const visible=computed(()=>props.customers.length?props.tasks.filter(task=>customerId(task)===active.value):props.tasks)
const currentName=computed(()=>lookup.value.get(active.value) || "")
provide(customerScopeKey,{enabled:computed(()=>props.customers.length>0),name:computed(()=>props.nameField?currentName.value:""),tabs,active})
function update(tasks:T[]){
 if(!props.customers.length){emit("update:tasks",tasks);return}
 const original=new Set(visible.value);const normalized=tasks.map(task=>{const editedName=props.nameField?task[props.nameField]:"";let id=(editedName?[...lookup.value].find(([,name])=>name===editedName)?.[0]:undefined) || customerId(task) || active.value;const row={...task,customer_id:id};if(props.nameField && !row[props.nameField])row[props.nameField]=lookup.value.get(id) || "";return row})
 const target=normalized.find(task=>task.customer_id!==active.value)?.customer_id
 const next:T[]=[];let inserted=false;for(const task of props.tasks){if(original.has(task)){if(!inserted){next.push(...normalized);inserted=true}}else next.push(task)}if(!inserted)next.push(...normalized)
 emit("update:tasks",next);if(target)active.value=target
}
async function load(){error.value="";try{all.value=(await listDictionaryItems("customer")).items}catch(cause){error.value=cause instanceof Error?cause.message:"客户加载失败。"}}
onMounted(()=>void load())
</script>
<template><section class="customer-task-tabs"><p v-if="error" role="alert">{{error}} <button type="button" @click="load">重试</button></p><slot :tasks="visible" :update="update" /></section></template>
<style scoped src="./CustomerTaskTabs.css"></style>
