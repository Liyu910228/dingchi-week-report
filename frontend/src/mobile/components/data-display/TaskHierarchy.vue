<script setup lang="ts" generic="T">
import SwipeDeleteHeading from "./SwipeDeleteHeading.vue"
import { taskPreviewLimitKey } from "@/mobile/shared/task-preview"
import { computed, inject, ref, watch } from "vue"
import { taskHierarchy } from "@/mobile/shared/task-hierarchy"
const props=defineProps<{rows:readonly T[];allRows?:readonly T[];deletable?:boolean;taskKey:(row:T)=>string;contentKey:(row:T)=>string;rowKey:(row:T)=>string;title:(row:T)=>string}>()
const emit=defineEmits<{remove:[rows:T[]]}>()
function removeRows(row:T,level:"task"|"content"|"row"){
 if(!props.deletable)return
 emit("remove",(props.allRows || props.rows).filter(item=>props.taskKey(item)===props.taskKey(row) && (level==="task" || (props.contentKey(item)===props.contentKey(row) && (level==="content" || props.rowKey(item)===props.rowKey(row))))))
}
const previewLimit=inject(taskPreviewLimitKey,undefined)
const showAll=ref(false)
const groups=computed(()=>taskHierarchy(props.rows,props.taskKey,props.contentKey))
watch(()=>groups.value.map(group=>group.key).join("|"),()=>{showAll.value=false})
</script>
<template>
 <div class="task-hierarchy mobile-task-cards">
  <details v-for="(group,index) in groups" :key="group.key" v-show="!previewLimit || showAll || index < previewLimit" class="task-group" data-mobile-task-card>
   <SwipeDeleteHeading class="task-group-heading" :enabled="deletable" @remove="removeRows(group.row, 'task')"><span class="task-number">任务 {{index+1}}</span><span class="task-group-title user-content">{{title(group.row) || '未填写工作任务'}}</span><span class="task-disclosure" aria-hidden="true" /></SwipeDeleteHeading>
   <div class="task-group-body">
    <div class="task-parent-fields"><slot name="task" :row="group.row" :index="rows.indexOf(group.row)" /></div>
    <details v-for="(content,contentIndex) in group.contents" :key="content.key" class="task-content-panel">
     <SwipeDeleteHeading class="task-child-heading" :enabled="deletable" @remove="removeRows(content.rows[0]!, 'content')"><span>工作内容 {{contentIndex+1}}</span><span class="task-child-count">{{content.rows.length}} 条明细</span><span class="child-disclosure" aria-hidden="true" /></SwipeDeleteHeading>
     <slot name="content" :row="content.rows[0]!" :index="rows.indexOf(content.rows[0]!)" />
     <details v-for="(row,rowIndex) in content.rows" :key="rowKey(row)" class="task-outcome-panel">
      <SwipeDeleteHeading class="task-child-heading" :enabled="deletable" @remove="removeRows(row, 'row')"><span class="outcome-heading-label"><span class="outcome-number">{{contentIndex+1}}.{{rowIndex+1}}</span><span>工作成果与进度</span></span><span class="child-disclosure" aria-hidden="true" /></SwipeDeleteHeading>
      <slot name="row" :row="row" :index="rows.indexOf(row)" />
     </details>
    </details>
   </div>
  </details>
  <div v-if="previewLimit && groups.length > previewLimit" class="task-preview-toggle"><button type="button" :aria-expanded="showAll" @click="showAll=!showAll">{{showAll ? '收起' : '展示更多'}}</button></div>
  <slot v-if="!groups.length" name="empty" />
 </div>
</template>
<style scoped src="./TaskHierarchy.css"></style>



