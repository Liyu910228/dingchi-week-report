<script setup lang="ts">
import { computed } from "vue"

import type { DirectoryGroup } from "../types"

import OrganizationChartNode from "./OrganizationChartNode.vue"

const props = withDefaults(
  defineProps<{
    groups?: DirectoryGroup[]
    selectedId?: string | null
    /** 让节点内容（例如用户/角色列表）默认折叠，并由点击分组节点切换。 */
    collapsible?: boolean
  }>(),
  { groups: () => [], selectedId: null, collapsible: false },
)

const emit = defineEmits<{
  select: [group: DirectoryGroup]
}>()

defineSlots<{
  node(props: {
    group: DirectoryGroup
    isExpanded: boolean
    toggle: () => void
  }): unknown
}>()

interface OrganizationGroupNode {
  group: DirectoryGroup
  children: OrganizationGroupNode[]
}

function idOf(value: string | number | null | undefined): string | null {
  return value === null || value === undefined || value === "" ? null : String(value)
}

const roots = computed<OrganizationGroupNode[]>(() => {
  const nodes = new Map<string, OrganizationGroupNode>()
  for (const group of props.groups) {
    nodes.set(String(group.id), { group, children: [] })
  }

  const rootNodes: OrganizationGroupNode[] = []
  for (const node of nodes.values()) {
    const parentId = idOf(node.group.parent_group_id)
    const parent = parentId ? nodes.get(parentId) : null
    if (parent) parent.children.push(node)
    else rootNodes.push(node)
  }

  const sortNodes = (items: OrganizationGroupNode[]) => {
    items.sort((left, right) => left.group.group_name.localeCompare(right.group.group_name, "zh-CN"))
    items.forEach((item) => sortNodes(item.children))
  }
  sortNodes(rootNodes)
  return rootNodes
})
</script>

<template>
  <div v-if="roots.length" class="organization-chart" aria-label="组织架构图">
    <div class="organization-chart__canvas">
      <OrganizationChartNode
        v-for="node in roots"
        :key="node.group.id"
        :node="node"
        :selected-id="selectedId"
        :collapsible="collapsible"
        @select="emit('select', $event)"
      >
        <template #node="slotProps">
          <slot name="node" v-bind="slotProps" />
        </template>
      </OrganizationChartNode>
    </div>
  </div>
  <div v-else class="organization-chart__empty">暂无组织分组</div>
</template>

<style scoped src="./OrganizationChart.css"></style>
