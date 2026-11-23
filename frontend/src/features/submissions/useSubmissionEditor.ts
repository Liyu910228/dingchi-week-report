import {computed,nextTick,onUnmounted,reactive,ref,watch} from "vue"
import {getErrorMessage} from "@/shared/api/errors"
import {useUnsavedChanges} from "@/shared/forms/useUnsavedChanges"
import {isSupportedTemplate,TEMPLATE_UNAVAILABLE_MESSAGE} from "@/features/weekly-report/template-support"
import {monthlySubmissionErrors} from "./monthly-validation"
import {previewSubmissionChange,createSubmissionChange,getSubmission,getSubmissionContext,saveSubmission,submitSubmission,getSubmissionChange,saveSubmissionChange,submitSubmissionChange} from "./api"
import type {SubmissionKind,SubmissionInput,SubmissionPart,SubmissionDetail,SubmissionChange,SubmissionContext} from "./types"
function today(){const d=new Date();d.setDate(d.getDate()-((d.getDay()+6)%7));return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`}
export function useSubmissionEditor(kind:SubmissionKind,readonly=false){
 const input=reactive<SubmissionInput>({month_key:`${new Date().getFullYear()}-${String(new Date().getMonth()+1).padStart(2,"0")}`,period_start:today(),parts:[]})
 const newChange=ref(false)
 const detail=ref<SubmissionDetail>(),change=ref<SubmissionChange>(),context=ref<SubmissionContext>()
 const loading=ref(true),busy=ref(false),error=ref(""),unavailable=ref(false),active=ref(""),generation=ref(0)
 const canEdit=computed(()=>!loading.value && !unavailable.value && (change.value?.can_edit ?? detail.value?.can_edit ?? true))
 const tabs=computed(()=>input.parts.map(p=>({id:p.role_code,name:p.role_name})))
 const tracker=useUnsavedChanges(()=>input,()=>!loading.value && !busy.value)
 const unsaved={...tracker,hasChanges:computed(()=>tracker.hasChanges.value || (newChange.value && !loading.value && !busy.value))}
 function apply(data:SubmissionDetail){detail.value=data;input.month_key=data.plan.month_key;input.period_start=data.plan.period_start || input.period_start;input.revision=data.plan.revision;input.parts=data.parts;generation.value++}
 function applyChange(data:SubmissionChange){change.value=data;input.change_reason=data.snapshot.change_reason || "";input.base_revision=data.change.base_revision;newChange.value=!data.change.id;input.month_key=data.plan.month_key;input.revision=data.change.revision;input.parts=data.snapshot.parts;generation.value++}
 async function gates(){
  if(readonly || kind!=="weekly")return
  const month=input.period_start?.slice(0,7) || input.month_key
  const data=await getSubmissionContext(kind,month)
  if(month!==input.period_start?.slice(0,7))return
  context.value=data;input.month_key=month
  for(const part of input.parts){const config=data.positions.find(p=>p.role_code===part.role_code);part.monthly_plan=config?.monthly_plan;part.monthly_approved=config?.monthly_approved;part.monthly_message=config?.monthly_message}
 }
 async function load(id:string,changeId:string,isNewChange=false){
  loading.value=true;error.value=""
  try{
   if(isNewChange)applyChange(await previewSubmissionChange(id))
   else if(changeId)applyChange(await getSubmissionChange(changeId))
   else if(id)apply(await getSubmission(kind,id))
   else {context.value=await getSubmissionContext(kind);input.parts=context.value.positions.map(p=>({...p,payload:{summary:"",tasks:[],items:[],metrics:[],daily_tasks:[]}}))}
   if(input.parts.some(p=>!isSupportedTemplate(p.template_code)))throw Error(TEMPLATE_UNAVAILABLE_MESSAGE)
   active.value=input.parts.find(p=>p.id===id)?.role_code || input.parts[0]?.role_code || ""
   if(!readonly && !isNewChange && (!id && !changeId || kind==="weekly" && detail.value?.can_edit))await gates()
  }catch(cause){error.value=getErrorMessage(cause);unavailable.value=true}
  finally{loading.value=false;await nextTick();unsaved.markSaved()}
 }
 async function save(submit:boolean){
  if(!canEdit.value || busy.value)return ""
  if(submit && kind==="monthly"){
   const errors=monthlySubmissionErrors(input.parts)
   if(errors.length){active.value=errors[0]!.roleCode;error.value=errors.map(item=>item.message).join("\n");return ""}
  }
  busy.value=true;error.value=""
  try{
   let id=""
   if(newChange.value && change.value){applyChange(await createSubmissionChange(change.value.plan.id,input,submit));id=change.value.change.id}
   else if(change.value){applyChange(await saveSubmissionChange(change.value.change.id,input));id=change.value.change.id;if(submit)applyChange(await submitSubmissionChange(id))}
   else {apply(await saveSubmission(kind,input,detail.value?.plan.id));id=detail.value!.plan.id;if(submit)apply(await submitSubmission(kind,id))}
   await nextTick();unsaved.markSaved();return id
  }catch(cause){error.value=getErrorMessage(cause);return ""}
  finally{busy.value=false}
 }
 function update(part:SubmissionPart,payload:SubmissionPart["payload"]){part.payload={...part.payload,...payload}}
 watch(()=>input.period_start,()=>{if(!readonly && !loading.value && kind==="weekly"){error.value="";void gates().catch(cause=>{error.value=getErrorMessage(cause);for(const part of input.parts)part.monthly_approved=false})}})
 onUnmounted(()=>{input.parts=[];input.change_reason="";change.value=undefined;newChange.value=false})
 return {newChange,input,detail,change,context,loading,busy,error,unavailable,active,generation,canEdit,tabs,unsaved,load,save,update}
}
