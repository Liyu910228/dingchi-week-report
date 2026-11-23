<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"

import type { DirectoryGroup } from "../types"

interface TreeRow {
  group: DirectoryGroup
  depth: number
  hasChildren: boolean
}

const props = withDefaults(
  defineProps<{
    modelValue?: string | null
    groups?: DirectoryGroup[]
    disabled?: boolean
    emptyLabel?: string
    allowEmpty?: boolean
    valueField?: "id" | "group_code"
  }>(),
  {
    modelValue: null,
    groups: () => [],
    disabled: false,
    emptyLabel: "未分组",
    allowEmpty: true,
    valueField: "id",
  },
)

const emit = defineEmits<{
  "update:modelValue": [value: string | null]
}>()

const root = ref<HTMLElement | null>(null)
const popup = ref<HTMLElement | null>(null)
const popupStyle = ref<Record<string,string>>({})
function positionPopup(event?:Event) {
  if(!isOpen.value || (event?.target instanceof Node && popup.value?.contains(event.target)))return
  const rect=root.value?.getBoundingClientRect();if(!rect)return
  const below=window.innerHeight-rect.bottom-14,above=rect.top-14
  const down=below>=160 || below>=above
  const height=Math.max(0,Math.min(260,down?below:above))
  popupStyle.value={left:`${Math.max(8,Math.min(rect.left,window.innerWidth-rect.width-8))}px`,width:`${Math.min(rect.width,window.innerWidth-16)}px`,maxHeight:`${height}px`,...(down?{top:`${rect.bottom+6}px`}:{bottom:`${window.innerHeight-rect.top+6}px`})}
}
const isOpen = ref(false)
watch(isOpen,async open=>{if(open){await nextTick();positionPopup()}})
const expandedIds = ref(new Set<string>())

function idOf(value: string | number | null | undefined): string | null {
  return value === null || value === undefined || value === "" ? null : String(value)
}

function valueOf(group: DirectoryGroup): string {
  return props.valueField === "group_code" ? group.group_code : String(group.id)
}

const selectedGroup = computed(
  () => props.groups.find((group) => valueOf(group) === props.modelValue) ?? null,
)

const childrenMap = computed(() => {
  const map = new Map<string | null, DirectoryGroup[]>()
  const ids = new Set(props.groups.map((group) => idOf(group.id)).filter((id): id is string => Boolean(id)))
  for (const group of props.groups) {
    const parentId = idOf(group.parent_group_id)
    const resolvedParentId = parentId && ids.has(parentId) ? parentId : null
    const children = map.get(resolvedParentId) ?? []
    children.push(group)
    map.set(resolvedParentId, children)
  }
  for (const children of map.values()) {
    children.sort((left, right) => left.group_name.localeCompare(right.group_name, "zh-CN"))
  }
  return map
})

const treeRows = computed<TreeRow[]>(() => {
  const rows: TreeRow[] = []
  const visited = new Set<string>()
  const append = (parentId: string | null, depth: number) => {
    for (const group of childrenMap.value.get(parentId) ?? []) {
      const groupId = idOf(group.id)
      if (!groupId || visited.has(groupId)) continue
      visited.add(groupId)
      const children = childrenMap.value.get(groupId) ?? []
      rows.push({ group, depth, hasChildren: children.length > 0 })
      if (children.length && expandedIds.value.has(groupId)) append(groupId, depth + 1)
    }
  }
  append(null, 0)
  return rows
})

watch(
  () => props.groups,
  (groups) => {
    const ids = new Set(groups.map((group) => idOf(group.id)).filter((id): id is string => Boolean(id)))
    const next = new Set([...expandedIds.value].filter((id) => ids.has(id)))
    for (const group of groups) {
      const groupId = idOf(group.id)
      if (groupId && childrenMap.value.has(groupId)) next.add(groupId)
    }
    expandedIds.value = next
  },
  { immediate: true, deep: true },
)

function toggleOpen() {
  if (!props.disabled) isOpen.value = !isOpen.value
}

function toggleGroup(group: DirectoryGroup) {
  const groupId = idOf(group.id)
  if (!groupId) return
  const next = new Set(expandedIds.value)
  if (next.has(groupId)) next.delete(groupId)
  else next.add(groupId)
  expandedIds.value = next
}

function select(value: string | null) {
  emit("update:modelValue", value)
  isOpen.value = false
}

function handleDocumentPointerDown(event: PointerEvent) {
  if (!root.value?.contains(event.target as Node) && !popup.value?.contains(event.target as Node)) isOpen.value = false
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === "Escape") isOpen.value = false
}

onMounted(() => {
  window.addEventListener("resize",positionPopup)
  window.addEventListener("scroll",positionPopup,true)
  document.addEventListener("pointerdown", handleDocumentPointerDown)
  document.addEventListener("keydown", handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener("resize",positionPopup)
  window.removeEventListener("scroll",positionPopup,true)
  document.removeEventListener("pointerdown", handleDocumentPointerDown)
  document.removeEventListener("keydown", handleKeydown)
})
</script>

<template>
  <div ref="root" class="group-tree-select" :class="{ 'is-open': isOpen, 'is-disabled': disabled }">
    <button
      class="group-tree-select__trigger"
      type="button"
      :aria-expanded="isOpen"
      :disabled="disabled"
      @click="toggleOpen"
    >
      <span>{{ selectedGroup?.group_name || emptyLabel }}</span>
      <span class="group-tree-select__chevron" aria-hidden="true"></span>
    </button>

    <Teleport to="body"><div v-if="isOpen" ref="popup" :style="popupStyle" class="group-tree-select__popover" role="tree">
      <button
        v-if="allowEmpty"
        class="group-tree-select__empty"
        :class="{ 'is-selected': !modelValue }"
        type="button"
        @click="select(null)"
      >
        {{ emptyLabel }}
      </button>
      <div
        v-for="row in treeRows"
        :key="row.group.id"
        class="group-tree-select__row"
        :class="{ 'is-selected': modelValue === valueOf(row.group) }"
        :style="{ '--tree-depth': row.depth }"
        role="treeitem"
        :aria-level="row.depth + 1"
      >
        <button
          class="group-tree-select__toggle"
          type="button"
          :disabled="!row.hasChildren"
          :aria-label="row.hasChildren ? '展开或折叠下级分组' : '无下级分组'"
          @click.stop="toggleGroup(row.group)"
        >
          {{ row.hasChildren ? (expandedIds.has(String(row.group.id)) ? '−' : '+') : '·' }}
        </button>
        <button class="group-tree-select__label" type="button" @click="select(valueOf(row.group))">
          {{ row.group.group_name }}
        </button>
      </div>
      <p v-if="!treeRows.length" class="group-tree-select__empty-state">暂无可用分组</p>
    </div></Teleport>
  </div>
</template>

<style scoped src="./GroupTreeSelect.css"></style>
