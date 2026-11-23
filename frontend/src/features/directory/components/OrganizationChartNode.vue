<script setup lang="ts">
import { ref } from "vue"

import type { DirectoryGroup } from "../types"

interface OrganizationGroupNode {
  group: DirectoryGroup
  children: OrganizationGroupNode[]
}

defineOptions({ name: "OrganizationChartNode" })

const props = withDefaults(defineProps<{
  node: OrganizationGroupNode
  selectedId?: string | null
  collapsible?: boolean
}>(), {
  selectedId: null,
  collapsible: false,
})

const isExpanded = ref(!props.collapsible)

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

function toggleNode() {
  if (props.collapsible) isExpanded.value = !isExpanded.value
  emit("select", props.node.group)
}
</script>

<template>
  <div class="organization-branch">
    <div class="organization-node-wrap">
      <div
        class="organization-node"
        :class="{ 'is-selected': String(props.selectedId) === String(props.node.group.id) }"
        role="button"
        tabindex="0"
        :aria-expanded="props.collapsible ? isExpanded : undefined"
        @click="toggleNode"
        @keydown.enter.prevent="toggleNode"
        @keydown.space.prevent="toggleNode"
      >
        <slot name="node" :group="props.node.group" :is-expanded="isExpanded" :toggle="toggleNode">
          <strong>{{ props.node.group.group_name }}</strong>
        </slot>
        <span v-if="props.collapsible" class="organization-node__toggle" aria-hidden="true">
          {{ isExpanded ? "−" : "+" }}
        </span>
      </div>
    </div>
    <div v-if="props.node.children.length" class="organization-children">
      <OrganizationChartNode
        v-for="child in props.node.children"
        :key="child.group.id"
        :node="child"
        :selected-id="props.selectedId"
        :collapsible="props.collapsible"
        @select="emit('select', $event)"
      >
        <template #node="slotProps">
          <slot name="node" v-bind="slotProps" />
        </template>
      </OrganizationChartNode>
    </div>
  </div>
</template>

<style scoped src="./OrganizationChartNode.css"></style>
