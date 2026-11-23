<script setup lang="ts">
import { computed, ref } from "vue"
import { CalendarDays } from "lucide-vue-next"

const props = defineProps<{
  start: string
  end: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  "update:start": [value: string]
}>()

const periodInput = ref<HTMLInputElement | null>(null)
const displayStart = computed(() => formatDisplayDate(props.start))
const displayEnd = computed(() => formatDisplayDate(props.end))

function formatDisplayDate(value: string) {
  return value ? value.slice(0, 10).replaceAll("-", ".") : "—"
}

function openPicker() {
  if (props.disabled) return
  const input = periodInput.value
  if (!input) return
  const picker = input as HTMLInputElement & { showPicker?: () => void }
  if (picker.showPicker) {
    picker.showPicker()
  } else {
    input.focus()
    input.click()
  }
}

function monday(value: string) {
  const date = new Date(`${value}T00:00:00`)
  if (Number.isNaN(date.getTime())) return ""
  const day = date.getDay() || 7
  date.setDate(date.getDate() - day + 1)
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const dayValue = String(date.getDate()).padStart(2, "0")
  return `${date.getFullYear()}-${month}-${dayValue}`
}

function isMonday(value: string) {
  const date = new Date(`${value}T00:00:00`)
  return !Number.isNaN(date.getTime()) && (date.getDay() || 7) === 1
}

function handleChange(event: Event) {
  const input = event.target as HTMLInputElement
  const value = input.value
  if (!value || !isMonday(value)) {
    // Native date inputs still allow manual typing in some browsers even
    // when step=7 is set. Reject those values so this control can never
    // emit a non-Monday period.
    input.value = props.start.slice(0, 10)
    return
  }
  const normalized = monday(value)
  if (normalized) emit("update:start", normalized)
}
</script>

<template>
  <div class="week-period-picker" :class="{ 'is-disabled': disabled }">
    <button
      class="week-period-picker__trigger"
      type="button"
      :disabled="disabled"
      aria-label="选择周报周期（仅可选择周一）"
      @click="openPicker"
    >
      <span>本周</span>
      <strong>{{ displayStart }} - {{ displayEnd }}</strong>
      <CalendarDays class="period-calendar" :size="17" :stroke-width="2" aria-hidden="true" />
    </button>
    <input
      ref="periodInput"
      class="week-period-picker__input"
      :value="start"
      :disabled="disabled"
      min="2000-01-03"
      max="2100-12-27"
      step="7"
      type="date"
      tabindex="-1"
      aria-hidden="true"
      @change="handleChange"
    />
  </div>
</template>

<style scoped>
.week-period-picker { position: relative; }
.week-period-picker__trigger {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: inherit;
  gap: inherit;
  min-height: 100%;
  padding: 0;
  border: 0;
  color: inherit;
  background: transparent;
  font: inherit;
  text-align: inherit;
  cursor: pointer;
}
.week-period-picker__trigger:focus-visible { outline: 2px solid rgba(39, 120, 232, .52); outline-offset: 3px; }
.week-period-picker__trigger:disabled { cursor: default; }
.week-period-picker__trigger > span:first-child { color: #173b70; font-size: 13px; font-weight: 700; }
.week-period-picker__trigger strong { color: #1e5bab; font-size: 16px; font-weight: 700; }
.period-calendar { color: #1477e8; flex: 0 0 auto; }
.week-period-picker__input { position: absolute; width: 1px; height: 1px; overflow: hidden; opacity: 0; pointer-events: none; }
.week-period-picker.is-disabled { opacity: .82; }
</style>
