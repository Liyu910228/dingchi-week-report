import { defineStore } from "pinia"
import { ref,watch } from "vue"
import { useAuthStore } from "@/features/auth/store"
import { listTodos,markTodoRead } from "./api"
import type { TodoList } from "./types"
const empty=():TodoList=>({role_code:"",items:[],total:0,unread_count:0,pending_approval_count:0,page:1,page_size:10,total_pages:0})
export const useTodoStore=defineStore('todos',()=>{
 const auth=useAuthStore(),data=ref<TodoList>(empty()),busy=ref(false),error=ref(''),loaded=ref(false)
 let version=0
 function reset(){version++;data.value=empty();error.value='';loaded.value=false;busy.value=false}
 async function load(page=data.value.page){
  if(!auth.isAuthenticated)return
  const current=++version,user=auth.user?.id,role=auth.effectiveRole?.role_code;busy.value=true
  try{const result=await listTodos(page);if(current!==version || user!==auth.user?.id || role!==auth.effectiveRole?.role_code)return
   if(result.role_code!==role)throw new Error("待办职位信息已变更，请刷新后重试。")
   data.value=result;loaded.value=true;error.value=''
   if(result.total_pages && page>result.total_pages)await load(result.total_pages)
  }catch(cause){if(current===version)error.value=cause instanceof Error?cause.message:'待办加载失败。'}
  finally{if(current===version)busy.value=false}
 }
 async function read(id:string){
  const user=auth.user?.id,role=auth.effectiveRole?.role_code,current=version
  if(data.value.role_code!==role || !data.value.items.some(item=>item.id===id && auth.roles.some(assigned=>assigned.role_code===item.role_code)))return
  try{await markTodoRead(id);if(user===auth.user?.id && role===auth.effectiveRole?.role_code)await load()}
  catch(cause){if(current===version)error.value=cause instanceof Error?cause.message:'标记已读失败。'}
 }
 watch(()=>[auth.user?.id,auth.effectiveRole?.role_code],reset,{flush:'sync'})
 return {data,busy,error,loaded,load,read,reset}
})
