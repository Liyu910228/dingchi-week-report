import { computed,onMounted,onUnmounted,ref } from "vue"

export function useTodoPosition(){
 const width=ref(innerWidth),height=ref(innerHeight)
 const x=ref(Math.max(12,innerWidth-80)),y=ref(Math.max(12,innerHeight-(innerWidth<=760?140:80)))
 let startX=0,startY=0,originX=0,originY=0,moved=false,dragged=false
 function clamp(){
  if(innerWidth<1 || innerHeight<1)return
  width.value=innerWidth;height.value=innerHeight
  if(!dragged){x.value=Math.max(12,innerWidth-80);y.value=Math.max(12,innerHeight-(innerWidth<=760?140:80));return}
  x.value=Math.max(12,Math.min(x.value,innerWidth-68));y.value=Math.max(12,Math.min(y.value,innerHeight-68))
 }
 function start(event:PointerEvent){if(event.button!==0)return;startX=event.clientX;startY=event.clientY;originX=x.value;originY=y.value;moved=false;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)}
 function move(event:PointerEvent){if(!(event.currentTarget as HTMLElement).hasPointerCapture(event.pointerId))return;const dx=event.clientX-startX,dy=event.clientY-startY;if(Math.abs(dx)+Math.abs(dy)>5)moved=true;if(moved){dragged=true;x.value=originX+dx;y.value=originY+dy;clamp()}}
 function end(event:PointerEvent){(event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId);return !moved}
 const anchor=computed(()=>({left:`${x.value}px`,top:`${y.value}px`}))
 const above=computed(()=>y.value-24>=height.value-y.value-80)
 const panel=computed(()=>{
  const w=Math.min(370,width.value-24),left=Math.max(12,Math.min(x.value+56-w,width.value-w-12))
  const available=above.value?y.value-24:height.value-y.value-80
  return {left:`${left}px`,width:`${w}px`,maxHeight:`${Math.min(520,Math.max(120,available))}px`,
   ...(above.value?{bottom:`${height.value-y.value+12}px`}:{top:`${y.value+68}px`}),
   '--todo-arrow-offset':`${Math.max(20,Math.min(w-20,x.value+28-left))}px`}
 })
 onMounted(()=>{clamp();window.addEventListener('resize',clamp)});onUnmounted(()=>window.removeEventListener('resize',clamp))
 return {anchor,panel,above,start,move,end}
}
