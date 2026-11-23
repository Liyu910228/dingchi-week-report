import {defineStore} from "pinia"
import {ref,watch} from "vue"
import {useAuthStore} from "@/features/auth/store"

export const defaultContentFontSize=14
export const minimumContentFontSize=10
export const maximumContentFontSize=24

function normalizeSize(value:number){
 return Number.isFinite(value)?Math.max(minimumContentFontSize,Math.min(maximumContentFontSize,Math.round(value))):defaultContentFontSize
}
/** 按登录用户在本浏览器记忆，仅设置用户内容字号变量，不改变页面根字号。 */
export const useContentTypography=defineStore("content-typography",()=>{
 const auth=useAuthStore(),size=ref(defaultContentFontSize)
 function apply(){document.documentElement.style.setProperty("--user-content-font-size",`${size.value}px`)}
 function key(){return `dingchi.user-content-font-size:${auth.user?.id || ""}`}
 watch(()=>auth.user?.id,()=>{
  let saved=defaultContentFontSize
  try {const raw=auth.user?.id?localStorage.getItem(key()):null;if(raw!==null)saved=normalizeSize(Number(raw))}catch{/* 存储不可用时仍允许本次调整。 */}
  size.value=saved;apply()
 },{immediate:true,flush:"sync"})
 watch(size,()=>{
  apply()
  if(auth.user?.id)try{localStorage.setItem(key(),String(size.value))}catch{/* 不阻断页面。 */}
 },{flush:"sync"})
 function setSize(value:number){size.value=normalizeSize(value)}
 function reset(){setSize(defaultContentFontSize)}
 return {size,setSize,reset}
})
