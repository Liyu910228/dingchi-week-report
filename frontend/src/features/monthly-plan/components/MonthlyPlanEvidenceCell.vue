<script setup lang="ts">
import {ref} from "vue"
import TaskEvidenceDialog from "@/features/weekly-report/components/TaskEvidenceDialog.vue"
import type {MonthlyPlanTask} from "@/features/weekly-report/monthly-plan/types"
import type {TaskAttachment} from "@/features/weekly-report/task-draft"
const props=defineProps<{task:MonthlyPlanTask;readonly?:boolean}>()
const emit=defineEmits<{patch:[value:Partial<MonthlyPlanTask>]}>()
const open=ref(false)
function save(links:string,attachments:TaskAttachment[]){
 if(props.readonly)return
 emit('patch',{document_links:links,attachments});open.value=false
}
</script>
<template>
<button class="evidence-text user-content" type="button" :aria-label="`${readonly?'查看':'编辑'}相关文档链接或佐证材料`" @click="open=true">{{task.document_links || (readonly?'—':'点击填写相关文档链接或佐证材料')}}</button>
<button v-if="!readonly || task.attachments?.length" class="link-button attachment-button" type="button" @click="open=true">{{task.attachments?.length ? `${task.attachments.length} 个附件` : '管理附件'}}</button>
<TaskEvidenceDialog :open="open" :links="task.document_links || ''" :attachments="task.attachments || []" :readonly="readonly" @close="open=false" @save="save" />
</template>
<style scoped src="./MonthlyPlanEvidenceCell.css"></style>
