import { computed, watch } from "vue"
import type { SubmissionInput } from "./types"
import type { DailyWorkTask } from "@/features/weekly-report/types"
export function useCommonDailySummary(input:SubmissionInput){
 const primary=computed(()=>input.parts.find(part=>part.detail) || input.parts[0])
 const report=computed(()=>({id:primary.value?.detail?.report.id || '',period_start:input.period_start || '',period_end:endOfWeek(input.period_start || '') || primary.value?.detail?.report.period_end || ''}))
 const tasks=computed<DailyWorkTask[]>(()=>input.parts.flatMap(part=>(part.payload.daily_tasks || part.detail?.daily_tasks || []).map(task=>({id:task.id || `draft-${task.work_date}`,report_id:part.detail?.report.id || '',work_date:task.work_date,work_content:task.work_content,created_at:'',updated_at:part.detail?.daily_tasks.find(row=>row.id===task.id)?.updated_at || ''}))))
 watch(()=>input.period_start,(next,previous)=>{
  if(!next || !previous || next===previous)return
  const offset=Date.parse(`${next}T00:00:00Z`)-Date.parse(`${previous}T00:00:00Z`)
  if(!Number.isFinite(offset))return
  for(const part of input.parts){
   if(!part.payload.daily_tasks)continue
   part.payload.daily_tasks=part.payload.daily_tasks.map(task=>{
    const date=Date.parse(`${task.work_date}T00:00:00Z`)
    return Number.isFinite(date)?{...task,work_date:new Date(date+offset).toISOString().slice(0,10)}:task
   })
  }
 },{flush:'sync'})
 function update(value:DailyWorkTask[]){
  const owners=new Map(input.parts.flatMap(part=>(part.payload.daily_tasks || part.detail?.daily_tasks || []).filter(task=>task.id).map(task=>[task.id!,part.role_code] as const)))
  for(const part of input.parts)part.payload={...part.payload,daily_tasks:value.filter(task=>(owners.get(task.id) || primary.value?.role_code)===part.role_code).map(task=>({id:task.id.startsWith('draft-')?undefined:task.id,work_date:task.work_date,work_content:task.work_content}))}
 }
 return {report,tasks,update}
}
function endOfWeek(start:string){if(!start)return '';const date=new Date(start+'T00:00:00');date.setDate(date.getDate()+6);return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`}
