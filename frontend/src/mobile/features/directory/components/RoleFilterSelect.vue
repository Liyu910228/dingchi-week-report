<script setup lang="ts">
import { onMounted, ref } from "vue"
import { listRoleOptions } from "../api"
import type { DirectoryRoleOption } from "../types"
const selected = defineModel<string>({ default: "" })
defineProps<{ disabled?: boolean }>()
const roles = ref<DirectoryRoleOption[]>([])
const loading = ref(false), error = ref("")
async function load() {
  loading.value = true; error.value = ""
  try { roles.value = (await listRoleOptions()).items }
  catch (cause) { error.value = cause instanceof Error ? cause.message : "职位选项加载失败。" }
  finally { loading.value = false }
}
onMounted(() => void load())
</script>
<template>
  <span class="role-filter-select">
    <select v-model="selected" :disabled="disabled || loading" aria-label="职位筛选">
      <option value="">{{ loading ? '正在加载职位…' : '全部职位' }}</option>
      <option v-for="role in roles" :key="role.role_code" :value="role.role_code">{{ role.role_name }}</option>
    </select>
    <span v-if="error" class="role-filter-error" role="alert">{{ error }} <button type="button" @click="load">重试</button></span>
  </span>
</template>
<style scoped src="./RoleFilterSelect.css"></style>
