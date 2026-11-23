<script setup lang="ts">
import {computed,nextTick,onBeforeUnmount,onMounted,ref,useId,watch} from "vue"
import {useFloatingPanelDrag} from "../useFloatingPanelDrag"
const props=defineProps<{hasReason?:boolean;busy?:boolean}>()
type Panel="approval"|"reason"
const active=ref<Panel|null>(null)
const anchor=ref<HTMLElement|null>(null),panel=ref<HTMLElement|null>(null),rail=ref<HTMLElement|null>(null)
const approvalButton=ref<HTMLButtonElement|null>(null),reasonButton=ref<HTMLButtonElement|null>(null)
const rightInset=ref(12),panelId=`monthly-floating-${useId()}`
const title=computed(()=>active.value==='reason'?'变更原因':'审批流程')
const drag=useFloatingPanelDrag(rail,panel,rightInset,()=>Boolean(props.busy),()=>active.value!==null)
watch(active,()=>void drag.reflow())
let observer:ResizeObserver|undefined
function updateInset(){
 let inset=Math.max(0,window.innerWidth-document.documentElement.clientWidth)
 // 同时避让贴近窗口右缘的嵌套滚动区域的滚动条。
 for(let node=anchor.value?.parentElement;node;node=node.parentElement){
  const rect=node.getBoundingClientRect()
  if(rect.right>=document.documentElement.clientWidth-24 && /auto|scroll/.test(getComputedStyle(node).overflowY) && node.scrollHeight>node.clientHeight){
   inset=Math.max(inset,window.innerWidth-rect.left-node.clientLeft-node.clientWidth)
  }
 }
 rightInset.value=Math.max(12,inset+12)
 void drag.reflow()
}
async function close(restoreFocus=true){
 const previous=active.value;active.value=null
 if(restoreFocus){await nextTick();(previous==='reason'?reasonButton.value:approvalButton.value)?.focus()}
}
async function toggle(value:Panel){
 if(props.busy)return
 if(active.value===value){await close();return}
 updateInset();active.value=value;await nextTick();panel.value?.focus()
}
function outside(event:PointerEvent){
 const target=event.target as Node
 if(active.value && !panel.value?.contains(target) && !rail.value?.contains(target))void close(false)
}
function keydown(event:KeyboardEvent){if(active.value && event.key==='Escape'){event.preventDefault();void close()}}
watch(()=>props.hasReason,value=>{if(!value && active.value==='reason')void close()})
onMounted(()=>{
 updateInset();window.addEventListener('resize',updateInset)
 document.addEventListener('pointerdown',outside);document.addEventListener('keydown',keydown)
 observer=new ResizeObserver(updateInset);observer.observe(document.documentElement)
 for(let node=anchor.value?.parentElement;node;node=node.parentElement)observer.observe(node)
})
onBeforeUnmount(()=>{observer?.disconnect();window.removeEventListener('resize',updateInset);document.removeEventListener('pointerdown',outside);document.removeEventListener('keydown',keydown)})
</script>
<template>
 <span ref="anchor" class="monthly-floating-anchor" aria-hidden="true" />
 <Teleport to="body">
  <div class="monthly-floating" :style="{'--monthly-floating-right':`${rightInset}px`}">
   <nav ref="rail" class="monthly-floating-rail" :class="{'is-dragging':drag.dragging.value}" :style="drag.railStyle.value" aria-label="月度计划辅助信息" title="拖动可移动整组按钮" @pointerdown="drag.pointerdown" @click.capture="drag.click">
    <button ref="approvalButton" type="button" :class="{'is-active':active==='approval'}" :disabled="busy" :aria-expanded="active==='approval'" :aria-controls="panelId" @click="toggle('approval')">审批流程</button>
    <button v-if="hasReason" ref="reasonButton" type="button" :class="{'is-active':active==='reason'}" :disabled="busy" :aria-expanded="active==='reason'" :aria-controls="panelId" @click="toggle('reason')">变更原因</button>
   </nav>
   <section v-show="active" :id="panelId" ref="panel" class="monthly-floating-panel" :style="drag.panelStyle.value" role="region" :aria-label="title" tabindex="-1">
    <header class="monthly-floating-heading"><h2>{{title}}</h2><button type="button" :aria-label="`关闭${title}`" @click="close()">×</button></header>
    <div class="monthly-floating-content"><div v-show="active==='approval'"><slot name="approval" /></div><div v-show="active==='reason'"><slot name="reason" /></div></div>
   </section>
  </div>
 </Teleport>
</template>
<style scoped src="./MonthlyFloatingPanels.css"></style>
