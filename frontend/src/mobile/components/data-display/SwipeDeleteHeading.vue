<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from "vue"
const props=defineProps<{enabled?:boolean}>()
const emit=defineEmits<{remove:[]}>()
const heading=ref<HTMLElement|null>(null)
const offset=ref(0)
let startX=0,startY=0,initial=0,swiping=false,dragged=false
function start(event:TouchEvent){
 if(!props.enabled)return
 const touch=event.touches[0]!
 startX=touch.clientX;startY=touch.clientY;initial=offset.value;swiping=false;dragged=false
}
function move(event:TouchEvent){
 if(!props.enabled)return
 const touch=event.touches[0]!,dx=touch.clientX-startX,dy=touch.clientY-startY
 if(!swiping && Math.abs(dy)>Math.abs(dx))return
 if(Math.abs(dx)>10){swiping=true;dragged=true;event.preventDefault();event.stopPropagation();offset.value=Math.min(0,Math.max(-76,initial+dx))}
}
function end(){if(swiping)offset.value=offset.value < -32 ? -76 : 0;swiping=false}
function click(event:MouseEvent){if((event.target as Element).closest('.swipe-delete'))return;if(dragged || offset.value){event.preventDefault();event.stopPropagation();if(!dragged)offset.value=0;dragged=false}}
function remove(){offset.value=0;emit('remove')}
let host:HTMLElement|null=null
function own(event:TouchEvent){return (event.target as Element).closest("details")===host && !(event.target as Element).closest("input,textarea,select,button,a")}
const begin=(e:TouchEvent)=>{if(own(e))start(e)}
const slide=(e:TouchEvent)=>{if(own(e))move(e)}
onMounted(()=>{host=heading.value?.closest("details") || null;host?.addEventListener("touchstart",begin,{passive:true});host?.addEventListener("touchmove",slide,{passive:false});host?.addEventListener("touchend",end);host?.addEventListener("touchcancel",end)})
onBeforeUnmount(()=>{host?.removeEventListener("touchstart",begin);host?.removeEventListener("touchmove",slide);host?.removeEventListener("touchend",end);host?.removeEventListener("touchcancel",end)})
</script>
<template>
 <summary ref="heading" class="swipe-heading" @click.capture="click">
  <button v-if="enabled" v-show="offset<0" class="swipe-delete" type="button" aria-label="删除此项及其子项" @click.stop.prevent="remove">删除</button>
  <div class="swipe-heading-content" :style="{transform:`translateX(${offset}px)`}" :class="{'is-dragging':swiping}"><slot /></div>
 </summary>
</template>
<style scoped src="./SwipeDeleteHeading.css"></style>



