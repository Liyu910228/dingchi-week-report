<script setup lang="ts">
import type { Customer } from "@/features/dictionary"

defineProps<{
  customers: Customer[]
  isLoading?: boolean
}>()

defineEmits<{
  edit: [customer: Customer]
  delete: [customer: Customer]
}>()
</script>

<template>
  <div class="customer-catalog">
    <div v-if="isLoading" class="empty-card" aria-live="polite">
      正在加载客户数据…
    </div>
    <div v-else-if="!customers.length" class="empty-card">
      暂无客户数据，点击右上角「新增客户」开始维护。
    </div>
    <table v-else class="customer-table">
      <colgroup>
        <col class="customer-column-code" />
        <col />
        <col class="customer-column-status" />
        <col class="customer-column-order" />
        <col class="customer-column-actions" />
      </colgroup>
      <thead>
        <tr>
          <th scope="col">客户编号</th>
          <th scope="col">客户名称</th>
          <th scope="col">状态</th>
          <th scope="col" class="customer-table__num">排序</th>
          <th scope="col" class="customer-table__actions">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="customer in customers" :key="customer.id">
          <td>{{ customer.dict_code }}</td>
          <td>{{ customer.dict_name }}</td>
          <td>
            <span :class="['customer-table__status', `is-${customer.status}`]">
              {{ customer.status === "active" ? "启用" : "停用" }}
            </span>
          </td>
          <td class="customer-table__num">{{ customer.sort_order }}</td>
          <td class="customer-table__actions">
            <button class="ghost-button" type="button" @click="$emit('edit', customer)">编辑</button>
            <button class="ghost-button is-danger" type="button" @click="$emit('delete', customer)">
              删除
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped src="./CustomerCatalog.css"></style>
