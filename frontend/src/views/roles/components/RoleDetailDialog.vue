<script setup lang="ts">
import CustomerSelect from "@/features/directory/components/CustomerSelect.vue"
import { computed } from "vue"
import BaseDialog from "@/components/overlay/BaseDialog.vue"
import type { DictionaryItem } from "@/features/dictionary"
import type { DirectoryGroup, DirectoryRole } from "@/features/directory/types"

const props = defineProps<{
  open: boolean
  role: DirectoryRole | null
  scopeOptions: DictionaryItem[]
  templateOptions: DictionaryItem[]
  groupOptions: DirectoryGroup[]
}>()
const emit = defineEmits<{ close: []; edit: [role: DirectoryRole] }>()
const scopeName = computed(() => props.scopeOptions.find(item => item.dict_code === props.role?.scope)?.dict_name || props.role?.scope || "未配置")
const templateName = computed(() => props.templateOptions.find(item => item.dict_code === props.role?.report_template_code)?.dict_name || props.role?.report_template_code || "未配置")
const groupName = computed(() => props.groupOptions.find(item => item.group_code === props.role?.role_group_code)?.group_name || props.role?.role_group_code || "未分组")
</script>

<template>
  <BaseDialog :open="open" title="查看职位" width="620px" @close="emit('close')">
    <div v-if="role" class="role-detail">
      <div class="detail-profile">
        <div class="detail-identity">
          <h3>{{ role.role_name }}</h3>
          <p>{{ role.role_code }}</p>
        </div>
        <button class="secondary-button" type="button" @click="emit('edit', role)">编辑</button>
      </div>
      <dl class="detail-grid">
        <div><dt>所属分组</dt><dd>{{ groupName }}</dd></div>
        <div><dt>数据范围</dt><dd>{{ scopeName }}</dd></div>
        <div><dt>周报模板</dt><dd>{{ templateName }}</dd></div>
        <div><dt>状态</dt><dd>{{ role.status === 'active' ? '启用' : '停用' }}</dd></div>
        <div class="detail-description"><dt>负责的客户</dt><dd><CustomerSelect :model-value="role.customer_ids || []" disabled /></dd></div>
        <div class="detail-description"><dt>描述</dt><dd>{{ role.description || '未填写' }}</dd></div>
      </dl>
    </div>
    <template #actions>
      <button class="secondary-button" type="button" @click="emit('close')">关闭</button>
    </template>
  </BaseDialog>
</template>

<style scoped src="./RoleDetailDialog.css"></style>
