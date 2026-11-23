<script setup lang="ts">
import { computed } from "vue"

import OrganizationChart from "@/features/directory/components/OrganizationChart.vue"
import type { DirectoryRole } from "@/features/directory/types"
import type { DictionaryItem } from "@/features/dictionary"

const props = withDefaults(
  defineProps<{
    roles: DirectoryRole[]
    isLoading?: boolean
    activeRoleCode?: string
    scopeOptions?: DictionaryItem[]
    templateOptions?: DictionaryItem[]
    groupOptions?: import("@/features/directory/types").DirectoryGroup[]
  }>(),
  {
    isLoading: false,
    activeRoleCode: "",
    scopeOptions: () => [],
    templateOptions: () => [],
    groupOptions: () => [],
  },
)

defineEmits<{
  view: [role: DirectoryRole]
  edit: [role: DirectoryRole]
  delete: [role: DirectoryRole]
}>()

function dictionaryLabel(options: DictionaryItem[], code: string): string {
  return options.find((item) => item.dict_code === code)?.dict_name || code
}

function scopeLabel(scope: string): string {
  return dictionaryLabel(props.scopeOptions, scope)
}

function templateLabel(templateCode: string): string {
  return dictionaryLabel(props.templateOptions, templateCode)
}

const rolesByGroup = computed(() => {
  const result = new Map<string, DirectoryRole[]>()
  for (const role of props.roles) {
    result.set(role.role_group_code, [...(result.get(role.role_group_code) || []), role])
  }
  return result
})

const ungroupedRoles = computed(() => props.roles.filter((role) => !props.groupOptions.some((group) => group.group_code === role.role_group_code)))

function deleteDisabledReason(role: DirectoryRole): string {
  if (role.role_code === "system_admin") return "系统管理员职位受保护，不能删除"
  if (role.role_code === props.activeRoleCode) return "当前正在使用的职位不能删除"
  return ""
}
</script>

<template>
  <div class="role-catalog-layout">
    <div v-if="isLoading" class="dashboard-card empty-card" aria-live="polite">正在加载职位数据…</div>
    <OrganizationChart v-else :collapsible="true" :groups="groupOptions">
      <template #node="{ group, isExpanded }">
        <strong class="organization-role-group">{{ group.group_name }}</strong>
        <span class="organization-role-count">{{ rolesByGroup.get(group.group_code)?.length || 0 }} 个职位</span>
        <div
          v-if="isExpanded && rolesByGroup.get(group.group_code)?.length"
          class="organization-roles"
          @click.stop
        >
          <article v-for="role in rolesByGroup.get(group.group_code)" :key="role.id" class="organization-role"
            role="button" tabindex="0" :aria-label="`查看职位：${role.role_name}`"
            @click="$emit('view', role)"
            @keydown.enter.self.prevent="$emit('view', role)"
            @keydown.space.self.prevent="$emit('view', role)"
          >
            <span class="role-mark" aria-hidden="true">{{ role.role_name.slice(0, 1) }}</span>
            <span class="organization-role__content">
              <strong>{{ role.role_name }}</strong>
              <small>{{ templateLabel(role.report_template_code) }} · {{ scopeLabel(role.scope) }}</small>
            </span>
            <span class="organization-role__actions">
              <button type="button" @click.stop="$emit('edit', role)">编辑</button>
              <button
                class="is-danger"
                type="button"
                :disabled="Boolean(deleteDisabledReason(role))"
                :title="deleteDisabledReason(role)"
                @click.stop="$emit('delete', role)"
              >删除</button>
            </span>
          </article>
        </div>
      </template>
    </OrganizationChart>
    <section v-if="ungroupedRoles.length" class="ungrouped-roles">
      <strong>未分组职位</strong>
      <button v-for="role in ungroupedRoles" :key="role.id" type="button" @click="$emit('view', role)">
        {{ role.role_name }}
      </button>
    </section>
  </div>
</template>

<style scoped src="./RoleCatalog.css"></style>
