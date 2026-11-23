import { computed, ref } from "vue"
import { getSubmission } from "@/mobile/features/submissions/api"
import { getErrorMessage } from "@/shared/api/errors"
import type { DailyWorkTask, WeeklyReport } from "../types"
interface DailyEntry {report:WeeklyReport;tasks:DailyWorkTask[]}
export function useReportDailyEntry(onError:(message:string)=>void) {
 const open=ref(false),loading=ref(false)
 const entries=ref<DailyEntry[]>([])
 const current=computed(()=>entries.value[0])
 const report=computed(()=>current.value?.report || null)
 const tasks=computed(()=>entries.value.flatMap(item=>item.tasks))
 let generation=0
 async function show(value:WeeklyReport){
  if(loading.value)return
  const request=++generation
  loading.value=true;onError("")
  try{
   const detail=await getSubmission("weekly",value.id)
   if(request!==generation)return
   entries.value=detail.parts.flatMap(part=>part.detail?[{report:part.detail.report,tasks:part.detail.daily_tasks || []}]:[])
   if(!entries.value.length)throw new Error("未找到可填写每日工作总结的周报，请刷新列表后重试。")
   open.value=true
  }catch(error){if(request===generation)onError(getErrorMessage(error))}
  finally{if(request===generation)loading.value=false}
 }
 function close(){generation++;open.value=false;loading.value=false;entries.value=[]}
 function saved(task:DailyWorkTask){const owner=entries.value.find(entry=>entry.tasks.some(item=>item.id===task.id)) || current.value;if(!owner)return;const index=owner.tasks.findIndex(item=>item.id===task.id);if(index<0)owner.tasks.push(task);else owner.tasks.splice(index,1,task)}
 return {open,report,tasks,show,close,saved}
}

