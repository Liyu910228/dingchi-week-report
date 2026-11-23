<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"
const props=withDefaults(defineProps<{showEnd?:boolean;loading:boolean;hasMore:boolean;error:string;page:number;total:number}>(),{showEnd:true})
const emit=defineEmits<{more:[]}>()
const sentinel=ref<HTMLElement|null>(null)
let observer:IntersectionObserver|undefined
let frame=0
let scrollRoot:HTMLElement|null=null
function check(){
 if(!props.hasMore || props.loading || props.error || !sentinel.value)return
 const box=sentinel.value.getBoundingClientRect()
 const viewport=scrollRoot?.getBoundingClientRect()
 if(box.top<(viewport?.bottom ?? window.innerHeight)+160 && box.bottom>(viewport?.top ?? 0))emit('more')
}
watch(()=>[props.loading,props.page,props.hasMore],async()=>{
 await nextTick();cancelAnimationFrame(frame);frame=requestAnimationFrame(check)
})
onMounted(()=>{
 for(let node=sentinel.value?.parentElement;node && node!==document.body;node=node.parentElement){
  if(/auto|scroll/.test(getComputedStyle(node).overflowY)){scrollRoot=node;break}
 }
 observer=new IntersectionObserver(entries=>{if(entries.some(entry=>entry.isIntersecting))check()},{root:scrollRoot,rootMargin:'160px'})
 if(sentinel.value)observer.observe(sentinel.value)
 window.addEventListener('scroll',check,true)
})
onBeforeUnmount(()=>{observer?.disconnect();cancelAnimationFrame(frame);window.removeEventListener('scroll',check,true)})
</script>
<template>
 <div v-show="loading || hasMore || (showEnd !== false && total > 0)" ref="sentinel" class="infinite-list-footer" aria-live="polite">
  <span v-if="loading" role="status">正在加载…</span>
  <button v-else-if="hasMore" type="button" @click="emit('more')">{{error?'加载失败，点击重试':'加载更多'}}</button>
  <span v-else-if="showEnd !== false && total">已到底</span>
 </div>
</template>
<style scoped src="./InfiniteListFooter.css"></style>



