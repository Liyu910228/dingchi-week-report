<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import NoticeBridge from "@/mobile/components/feedback/NoticeBridge.vue";
import ScrollableTabs from "@/mobile/components/navigation/ScrollableTabs.vue";
import { monthlyBodies } from "@/mobile/features/submissions/template-registry";
import { getErrorMessage } from "@/shared/api/errors";
import MonthWeekPanel from "./MonthWeekPanel.vue";
import { getMonth } from "./api";
import type { MonthDetail } from "./types";
const route = useRoute();
const data = ref<MonthDetail>();
const busy = ref(false);
const error = ref("");
const active = ref("");
const expanded = ref<string[]>([]);
const tabs = computed(() => data.value?.monthly_parts.map(p => ({ id: p.role_code, name: p.role_name })) || []);
const selected = computed(() => data.value?.monthly_parts.find(p => p.role_code === active.value));
let generation = 0;
async function load() {
    const token = ++generation;
    busy.value = true;
    error.value = "";
    data.value = undefined;
    try {
        const result = await getMonth(String(route.params.employeeId), String(route.params.monthKey));
        if (token !== generation)
            return;
        data.value = result;
        active.value = result.monthly_parts[0]?.role_code || "";
        expanded.value = result.weeks.slice(-1).map(w => w.plan.id);
    }
    catch (e) {
        if (token === generation)
            error.value = getErrorMessage(e);
    }
    finally {
        if (token === generation)
            busy.value = false;
    }
}
function toggle(id: string) { expanded.value = expanded.value.includes(id) ? expanded.value.filter(x => x !== id) : [...expanded.value, id]; }
watch(() => [route.params.employeeId, route.params.monthKey], load, { immediate: true });
</script>
<template>
  <div class="month-detail">
    <NoticeBridge :warning-message="error" />
    <header class="dashboard-card month-heading">
      <h1 v-if="data">{{ data.month_key }} 月度周报 · {{ data.weeks[0]?.plan.employee_name }}</h1>
      <h1 v-else>月度周报</h1>
    </header>
    <p v-if="busy">正在加载月度周报…</p>
    <template v-else-if="data">
      <section class="dashboard-card month-role-workspace">
        <ScrollableTabs v-model="active" :items="tabs" />
        <template v-if="selected">
          <component v-if="selected.monthly_approved && monthlyBodies[selected.template_code]"
            :is="monthlyBodies[selected.template_code]" :part="selected"
            :month-key="data.month_key" readonly />
          <p v-else-if="!selected.monthly_approved" class="month-empty">该职位本月暂无审批通过的月度计划。</p>
          <p v-else class="month-empty">该月度计划的模板暂不支持展示，请联系管理员。</p>
          <div class="month-task-heading">
            <h2>工作任务</h2>
            <div class="month-actions">
              <button class="ghost-button" @click="expanded = data.weeks.map(w => w.plan.id)">展开全部</button>
              <button class="ghost-button" @click="expanded = []">折叠全部</button>
            </div>
          </div>
          <MonthWeekPanel v-for="(week, index) in data.weeks" :key="week.plan.id" :week="week" :week-number="index + 1"
            :role-code="active" :expanded="expanded.includes(week.plan.id)" @toggle="toggle(week.plan.id)" />
        </template>
      </section>
    </template>
    <button v-if="error && !busy" class="ghost-button" @click="load">重新加载</button>
  </div>
</template>

<style scoped src="./MonthReportDetail.css"></style>
