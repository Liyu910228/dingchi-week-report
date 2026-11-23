import {computed,nextTick,onBeforeUnmount,onMounted,ref,type CSSProperties,type Ref} from "vue"

type Point={x:number;y:number}
/** 只保存当前组件内的位置，不写入任何浏览器存储。 */
export function useFloatingPanelDrag(rail:Ref<HTMLElement|null>,panel:Ref<HTMLElement|null>,rightInset:Ref<number>,busy:()=>boolean,isOpen:()=>boolean){
 const position=ref<Point|null>(null),dragging=ref(false),panelStyle=ref<CSSProperties>({})
 let start:{id:number;pointer:Point;origin:Point}|null=null,ignoreClickUntil=0,observer:ResizeObserver|undefined
 const railStyle=computed<CSSProperties>(()=>position.value?{left:`${position.value.x}px`,top:`${position.value.y}px`,right:"auto",transform:"none"}:{})
 function bounds(){return {width:document.documentElement.clientWidth,height:document.documentElement.clientHeight}}
 function clamp(point:Point){
  const rect=rail.value?.getBoundingClientRect(),view=bounds()
  return {x:Math.max(12,Math.min(point.x,view.width-rightInset.value-(rect?.width || 36))),y:Math.max(12,Math.min(point.y,view.height-12-(rect?.height || 0)))}
 }
 async function reflow(){
  if(position.value)position.value=clamp(position.value)
  await nextTick()
  if(!position.value || !isOpen() || !panel.value || !rail.value){panelStyle.value={};return}
  const rect=rail.value.getBoundingClientRect(),view=bounds(),gap=10
  const leftSpace=rect.left-gap-12,rightSpace=view.width-rightInset.value-rect.right-gap
  const left=leftSpace>=rightSpace,width=Math.max(0,Math.min(380,left?leftSpace:rightSpace))
  const x=left?rect.left-gap-width:rect.right+gap
  panelStyle.value={left:`${Math.max(12,x)}px`,right:"auto",top:"12px",transform:"none",width:`${width}px`}
  await nextTick()
  const height=panel.value?.getBoundingClientRect().height || 0
  panelStyle.value={...panelStyle.value,top:`${Math.max(12,Math.min(rect.top+rect.height/2-height/2,view.height-height-12))}px`}
 }
 function pointerdown(event:PointerEvent){
  if(event.button!==0 || busy() || start || !rail.value)return
  const rect=rail.value.getBoundingClientRect()
  start={id:event.pointerId,pointer:{x:event.clientX,y:event.clientY},origin:{x:rect.left,y:rect.top}}
 }
 function pointermove(event:PointerEvent){
  if(!start || event.pointerId!==start.id)return
  const dx=event.clientX-start.pointer.x,dy=event.clientY-start.pointer.y
  if(!dragging.value && Math.hypot(dx,dy)<5)return
  if(!dragging.value){
   dragging.value=true
   try{rail.value?.setPointerCapture(event.pointerId)}catch{/* 指针已被取消时仍可清理本次拖动。 */}
  }
  event.preventDefault();position.value=clamp({x:start.origin.x+dx,y:start.origin.y+dy});void reflow()
 }
 function finish(event?:PointerEvent){
  if(!start || event && event.pointerId!==start.id)return
  if(dragging.value)ignoreClickUntil=performance.now()+250
  try{if(rail.value?.hasPointerCapture(start.id))rail.value.releasePointerCapture(start.id)}catch{/* 指针捕获可能已由浏览器释放。 */}
  start=null;dragging.value=false
 }
 function click(event:MouseEvent){
  if(performance.now()<ignoreClickUntil && event.detail!==0){event.preventDefault();event.stopImmediatePropagation();ignoreClickUntil=0}
 }
 function blur(){finish()}
 onMounted(()=>{
  window.addEventListener("pointermove",pointermove,{passive:false});window.addEventListener("pointerup",finish);window.addEventListener("pointercancel",finish);window.addEventListener("blur",blur)
  observer=new ResizeObserver(()=>void reflow());if(rail.value)observer.observe(rail.value)
 })
 onBeforeUnmount(()=>{observer?.disconnect();window.removeEventListener("pointermove",pointermove);window.removeEventListener("pointerup",finish);window.removeEventListener("pointercancel",finish);window.removeEventListener("blur",blur);finish()})
 return {dragging,railStyle,panelStyle,pointerdown,click,reflow}
}
