<script setup lang="ts">
import { onMounted,onUnmounted,ref,watch } from "vue"
import { isNavigationFailure,useRouter } from "vue-router"
import { ClipboardList } from "lucide-vue-next"
import CountBadge from "@/components/feedback/CountBadge.vue"
import { useAuthStore } from "@/features/auth/store"
import { formatDateTime } from "@/utils/date"
import { useTodoStore } from "../store"
import type { TodoItem } from "../types"
import { useTodoPosition } from "./useTodoPosition"
const auth=useAuthStore(),todos=useTodoStore(),router=useRouter(),position=useTodoPosition(),open=ref(false),going=ref(false)
let timer:ReturnType<typeof setInterval>|undefined
function refresh(){if(!document.hidden)void todos.load()}
watch(()=>[auth.user?.id,auth.effectiveRole?.role_code],()=>{open.value=false;todos.reset();refresh()},{immediate:true})
onMounted(()=>{timer=setInterval(refresh,30000);window.addEventListener('focus',refresh)})
onUnmounted(()=>{clearInterval(timer);window.removeEventListener('focus',refresh)})
async function go(item:TodoItem){
 if(item.source!=='weekly_report' && !auth.roles.some(role=>role.role_code===item.role_code)){todos.error='此待办所属职位已不可用，请刷新后重试。';return}
 going.value=true
 try{
  if(item.target.kind==='monthly_plan_approval'){
   const failure=await router.push({name:'monthly-plans',query:{tab:'approvals',approval_id:item.target.approval_id}})
   if(!isNavigationFailure(failure))open.value=false
  }else if(item.target.kind==='weekly_report'){
   const failure=await router.push({name:'weekly-report-new',query:{period_start:item.target.period_start}})
   if(!isNavigationFailure(failure))open.value=false
  }else todos.error='此待办暂不支持自动跳转。'
 }catch(cause){todos.error=cause instanceof Error?cause.message:'跳转失败。'}finally{going.value=false}
}
function toggle(){open.value=!open.value;if(open.value)void todos.load()}
</script>
<template><Teleport to="body"><div v-if="auth.isAuthenticated" class="todo-widget">
<button class="todo-launcher" :style="position.anchor.value" type="button" aria-label="待办事项" :aria-expanded="open" aria-controls="global-todo-panel" @pointerdown="position.start" @pointermove="position.move" @pointerup="position.end($event) && toggle()" @click="($event.detail===0) && toggle()"><ClipboardList :size="25" aria-hidden="true" /><CountBadge :count="todos.data.unread_count" /></button>
<section v-if="open" id="global-todo-panel" class="todo-panel" :class="{'todo-panel--above':position.above.value}" :style="position.panel.value" aria-label="待办事项列表">
<header><h2>待办事项 <span>{{todos.data.total}}</span></h2><button type="button" aria-label="折叠待办列表" @click="open=false">关闭</button></header>
<p v-if="todos.error" class="todo-error" role="alert">{{todos.error}} <button type="button" @click="todos.load()">重试</button></p>
<div class="todo-items" :aria-busy="todos.busy"><article v-for="item in todos.data.items" :key="item.id" :class="{'is-unread':!item.read_at}"><div class="todo-item-heading"><span v-if="!item.read_at" class="unread-dot" aria-label="未读" /><h3>{{item.title}}</h3></div><time>{{formatDateTime(item.created_at)}}</time><div class="todo-item-actions"><button type="button" :disabled="going" @click="go(item)">去处理</button><button v-if="!item.read_at" type="button" :disabled="todos.busy" @click="todos.read(item.id)">标记已读</button><span v-else>已读</span></div></article><p v-if="!todos.data.items.length" class="todo-empty">{{todos.busy?'正在加载…':'暂无待办事项'}}</p></div>
<footer><span>共 {{todos.data.total}} 条</span><div><button type="button" :disabled="todos.busy || todos.data.page<=1" @click="todos.load(todos.data.page-1)">上一页</button><span>{{todos.data.page}} / {{Math.max(1,todos.data.total_pages)}}</span><button type="button" :disabled="todos.busy || todos.data.page>=todos.data.total_pages" @click="todos.load(todos.data.page+1)">下一页</button></div></footer>
</section></div></Teleport></template>
<style scoped src="./TodoFloatingWidget.css"></style>
