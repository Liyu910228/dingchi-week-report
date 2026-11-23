<script setup lang="ts">
import { computed, nextTick, reactive, ref, watch } from "vue"

import BaseDialog from "@/mobile/components/overlay/BaseDialog.vue"
import NoticeBridge from "@/mobile/components/feedback/NoticeBridge.vue"
import type { Customer, CustomerMutationPayload } from "@/mobile/features/dictionary"

const props = withDefaults(
  defineProps<{
    open: boolean
    customer?: Customer | null
    isSaving?: boolean
  }>(),
  {
    customer: null,
    isSaving: false,
  },
)

const emit = defineEmits<{
  close: []
  submit: [payload: CustomerMutationPayload]
}>()

const emptyForm = (): CustomerMutationPayload => ({
  dict_code: "",
  dict_name: "",
  sort_order: 0,
  status: "active",
  description: "",
})

const form = reactive<CustomerMutationPayload>(emptyForm())
const formError = ref("")
const codeInput = ref<HTMLInputElement | null>(null)
const nameInput = ref<HTMLInputElement | null>(null)
const isEditing = computed(() => Boolean(props.customer))

watch(
  () => ({ open: props.open, customer: props.customer }),
  ({ open, customer }) => {
    if (!open) return
    Object.assign(form, customer ? toForm(customer) : emptyForm())
    formError.value = ""
    void nextTick(() => (customer ? nameInput.value : codeInput.value)?.focus())
  },
  { immediate: true },
)

function toForm(customer: Customer): CustomerMutationPayload {
  return {
    dict_code: customer.dict_code,
    dict_name: customer.dict_name,
    sort_order: customer.sort_order,
    status: customer.status,
    description: customer.description,
  }
}

function submitForm() {
  const dict_code = form.dict_code.trim()
  const dict_name = form.dict_name.trim()
  const description = (form.description || "").trim()
  const sortOrder = Number(form.sort_order ?? 0)
  if (!dict_code || !dict_name) {
    formError.value = "请填写客户编号和客户名称。"
    return
  }
  if (!isEditing.value && !/^[A-Za-z0-9]{1,64}$/.test(dict_code)) {
    formError.value =
      "客户编号仅支持英文字母和数字，长度为 1–64 个字符。"
    return
  }
  if (dict_name.length > 128) {
    formError.value = "客户名称不能超过 128 个字符。"
    return
  }
  if (description.length > 255) {
    formError.value = "客户说明不能超过 255 个字符。"
    return
  }
  if (!Number.isInteger(sortOrder) || sortOrder < 0) {
    formError.value = "排序值必须是非负整数。"
    return
  }
  formError.value = ""
  emit("submit", {
    dict_code,
    dict_name,
    sort_order: sortOrder,
    status: form.status === "inactive" ? "inactive" : "active",
    description,
  })
}
</script>

<template>
  <BaseDialog
    :busy="isSaving"
    :open="open"
    :title="isEditing ? '编辑客户' : '新增客户'"
    width="560px"
    @close="$emit('close')"
  >
    <form id="customer-editor-form" class="customer-form" @submit.prevent="submitForm">
      <NoticeBridge :warning-message="formError" />

      <div class="form-grid">
        <label>
          <span>客户编号</span>
          <input
            ref="codeInput"
            v-model="form.dict_code"
            autocomplete="off"
            maxlength="64"
            :pattern="isEditing ? undefined : '[A-Za-z0-9]{1,64}'"
            title="仅支持英文字母和数字，最多 64 个字符"
            placeholder="C001"
            :disabled="isEditing || isSaving"
          />
          <small v-if="isEditing" class="customer-form__hint">客户编号创建后不可修改。</small>
          <small v-else>仅支持英文字母和数字，最多 64 个字符。</small>
        </label>

        <label>
          <span>客户名称</span>
          <input
            ref="nameInput"
            v-model="form.dict_name"
            autocomplete="off"
            maxlength="128"
            placeholder="请输入客户名称"
            :disabled="isSaving"
          />
          <small>最多 128 个字符。</small>
        </label>

        <label>
          <span>状态</span>
          <select v-model="form.status" :disabled="isSaving">
            <option value="active">启用</option>
            <option value="inactive">停用</option>
          </select>
        </label>

        <label>
          <span>排序</span>
          <input
            v-model.number="form.sort_order"
            type="number"
            min="0"
            step="1"
            :disabled="isSaving"
          />
        </label>

        <label class="description-field">
          <span>客户说明</span>
          <textarea
            v-model="form.description"
            maxlength="255"
            placeholder="可选，简要说明客户背景或对接人"
            rows="3"
            :disabled="isSaving"
          ></textarea>
          <small>{{ (form.description || "").length }}/255</small>
        </label>
      </div>
    </form>

    <template #actions>
      <button class="secondary-button" type="button" :disabled="isSaving" @click="$emit('close')">
        取消
      </button>
      <button
        class="primary-button"
        form="customer-editor-form"
        type="submit"
        :disabled="isSaving"
      >
        {{ isSaving ? "保存中…" : isEditing ? "保存修改" : "创建客户" }}
      </button>
    </template>
  </BaseDialog>
</template>

<style scoped src="./CustomerEditorDialog.css"></style>
