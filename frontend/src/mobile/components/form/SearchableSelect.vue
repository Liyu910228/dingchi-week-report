<script setup lang="ts">
import { computed, nextTick, onMounted, onBeforeUnmount, ref, watch } from "vue"

type SearchableOption = {
  value: string
  label: string
  description?: string
  disabled?: boolean
  group?: string
}

const props = withDefaults(
  defineProps<{
    modelValue: string | string[]
    options: SearchableOption[]
    showSelectAll?: boolean
    multiple?: boolean
    placeholder?: string
    disabled?: boolean
    ariaLabel?: string
    validationMessage?: string
    optionsDisabled?: boolean
    showSelectionOrder?: boolean
    teleportMenu?: boolean
    menuClass?: string
  }>(),
  {
    multiple: false,
    placeholder: "请选择",
    disabled: false,
    ariaLabel: "选择",
    validationMessage: "",
    optionsDisabled: false,
    showSelectionOrder: false,
  },
)

const emit = defineEmits<{
  "update:modelValue": [value: string | string[]]
}>()

const rootRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const isOpen = ref(false)
const query = ref("")
const menuRef = ref<HTMLElement | null>(null)
const floatingStyle = ref<Record<string, string>>({})
async function positionMenu() {
  if (!props.teleportMenu || !isOpen.value) return
  await nextTick()
  const rect = rootRef.value?.getBoundingClientRect()
  const menu = menuRef.value
  if (!rect || !menu) return
  const width = Math.min(rect.width, window.innerWidth - 24)
  const below = window.innerHeight - rect.bottom - 16
  const above = below < 180 && rect.top > below
  const maxHeight = Math.max(80, Math.min(240, above ? rect.top - 20 : below))
  const height = Math.min(maxHeight, menu.scrollHeight + 2)
  floatingStyle.value = {
    position: "fixed", left: `${Math.max(12, Math.min(rect.left, window.innerWidth - width - 12))}px`,
    right: "auto", top: `${above ? Math.max(12, rect.top - height - 4) : rect.bottom + 4}px`,
    bottom: "auto", width: `${width}px`, maxHeight: `${maxHeight}px`, zIndex: "1200",
  }
}
watch([isOpen, query, () => props.options, () => props.modelValue], positionMenu)
onMounted(() => { window.addEventListener("resize", positionMenu); window.addEventListener("scroll", positionMenu, true) })
onBeforeUnmount(() => { window.removeEventListener("resize", positionMenu); window.removeEventListener("scroll", positionMenu, true) })

watch(() => props.validationMessage, () => {
  void nextTick(() => inputRef.value?.setCustomValidity(props.validationMessage))
}, { immediate: true })

const selectedValues = computed<string[]>(() => {
  if (props.multiple) {
    return Array.isArray(props.modelValue) ? props.modelValue : []
  }
  return typeof props.modelValue === "string" && props.modelValue ? [props.modelValue] : []
})

const selectableValues = computed(() => props.options.filter(option => !option.disabled).map(option => option.value))
const allSelected = computed(() => selectableValues.value.length > 0 && selectableValues.value.every(value => selectedValues.value.includes(value)))
function toggleAll() {
  if (props.disabled || props.optionsDisabled || !props.multiple) return
  emit("update:modelValue", allSelected.value ? selectedValues.value.filter(value => !selectableValues.value.includes(value)) : [...new Set([...selectedValues.value, ...selectableValues.value])])
}
const selectedOptions = computed(() =>
  selectedValues.value
    .map((value) => props.options.find((option) => option.value === value))
    .filter((option): option is SearchableOption => Boolean(option)),
)

const filteredOptions = computed(() => {
  const keyword = query.value.trim().toLocaleLowerCase()
  if (!keyword) return props.options
  return props.options.filter((option) =>
    [option.label, option.description || "", option.group || ""].some((value) =>
      value.toLocaleLowerCase().includes(keyword),
    ),
  )
})

const optionGroups = computed(() => {
  const groups = new Map<string, typeof props.options>()
  for (const option of filteredOptions.value) {
    const name = option.group || ""
    groups.set(name, [...(groups.get(name) || []), option])
  }
  return [...groups].map(([name, options]) => ({ name, options }))
})

function openList() {
  if (props.disabled) return
  isOpen.value = true
  nextTick(() => inputRef.value?.focus())
}

// 控件及候选项的 click 阻止外层 label 默认激活首个“移除”按钮。
function handleControlMouseDown(event: MouseEvent) {
  if (props.disabled) return
  // 点击已选名称或控件空白处时，保留输入框焦点，避免浏览器默认聚焦
  // 外层可聚焦单元格后触发 focusout，将刚打开的候选列表关闭。
  if (event.target !== inputRef.value) event.preventDefault()
  openList()
}

function isSelected(value: string) {
  return selectedValues.value.includes(value)
}

function selectOption(option: SearchableOption) {
  if (option.disabled || props.optionsDisabled) return
  if (props.multiple) {
    const values = selectedValues.value
    const next = isSelected(option.value)
      ? values.filter((value) => value !== option.value)
      : [...values, option.value]
    emit("update:modelValue", next)
    query.value = ""
    openList()
    return
  }
  emit("update:modelValue", option.value)
  query.value = ""
  isOpen.value = false
}

function removeOption(value: string) {
  if (props.disabled || props.optionsDisabled) return
  if (!props.multiple) {
    emit("update:modelValue", "")
    return
  }
  emit("update:modelValue", selectedValues.value.filter((item) => item !== value))
}

function clearSingle(event: MouseEvent) {
  event.preventDefault()
  event.stopPropagation()
  emit("update:modelValue", "")
  query.value = ""
  openList()
}

function handleFocusOut() {
  window.setTimeout(() => {
    if (!rootRef.value?.contains(document.activeElement) && !menuRef.value?.contains(document.activeElement)) isOpen.value = false
  }, 0)
}
</script>

<template>
  <div
    ref="rootRef"
    class="searchable-select"
    :class="{ 'searchable-select--disabled': disabled }"
    @focusout="handleFocusOut"
    @click.prevent
  >
    <div class="searchable-select__control" @mousedown="handleControlMouseDown" @click.prevent>
      <div class="searchable-select__chips">
        <span v-for="(option, index) in (multiple ? selectedOptions : [])" :key="option.value" class="searchable-select__chip">
          {{ showSelectionOrder ? `${index + 1}. ` : "" }}{{ option.label }}
          <button
            type="button"
            aria-label="移除已选项"
            @mousedown.stop.prevent
            :disabled="disabled || optionsDisabled"
            @click.stop.prevent="removeOption(option.value)"
          >
            移除
          </button>
        </span>
      <span v-if="!multiple && selectedOptions[0] && !query" class="searchable-select__selected">
        {{ selectedOptions[0].label }}
      </span>
      <input
        ref="inputRef"
        v-model="query"
        class="searchable-select__input"
        :aria-label="ariaLabel"
        :disabled="disabled"
        :placeholder="selectedOptions.length ? '' : placeholder"
        autocomplete="off"
        @focus="openList"
        @keydown.esc="isOpen = false"
      />
      </div>
      <button
        v-if="!multiple && selectedValues.length"
        class="searchable-select__clear"
        type="button"
        @mousedown.stop.prevent
        @click="clearSingle"
      >
        清除
      </button>
    </div>
    <Teleport to="body" :disabled="!teleportMenu">
    <div v-if="isOpen" ref="menuRef" class="searchable-select__menu" :class="menuClass" :style="teleportMenu ? floatingStyle : undefined" role="listbox">
      <button v-if="multiple && showSelectAll" class="searchable-select__select-all" type="button" :disabled="disabled || optionsDisabled || !selectableValues.length" @mousedown.prevent @click.stop.prevent="toggleAll">{{ allSelected ? '取消全选' : '全选' }}</button>
      <template v-for="group in optionGroups" :key="group.name">
      <div v-if="group.name" class="searchable-select__group">{{ group.name }}</div>
      <button
        v-for="option in group.options"
        :key="option.value"
        class="searchable-select__option"
        :class="{ 'searchable-select__option--selected': isSelected(option.value) }"
        type="button"
        role="option"
        :aria-selected="isSelected(option.value)"
        :disabled="option.disabled || optionsDisabled"
        @mousedown.prevent
        @click.stop.prevent="selectOption(option)"
      >
        <span>
          <strong :title="option.label">{{ option.label }}</strong>
          <small v-if="option.description" :title="option.description">{{ option.description }}</small>
        </span>
        <em v-if="isSelected(option.value)">已选</em>
      </button>
      </template>
      <p v-if="!filteredOptions.length" class="searchable-select__empty">暂无匹配项</p>
    </div>
    </Teleport>
  </div>
</template>

<style scoped src="./SearchableSelect.css"></style>


