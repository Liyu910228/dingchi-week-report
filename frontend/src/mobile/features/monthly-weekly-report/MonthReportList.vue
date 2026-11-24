<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/features/auth/store";
import NoticeBridge from "@/mobile/components/feedback/NoticeBridge.vue";
import { getErrorMessage } from "@/shared/api/errors";
import { listMonths } from "./api";
import type { MonthRow } from "./types";
import ScrollLoadMore from "@/mobile/components/navigation/ScrollLoadMore.vue";
import MonthReportFilters from "./MonthReportFilters.vue";
import MonthReportTable from "./MonthReportTable.vue";
const auth = useAuthStore();
const router = useRouter();
const month = ref("");
const person = ref("");
const position = ref("");
const view = ref("members");
const page = ref(1);
const pages = ref(0);
const total = ref(0);
const rows = ref<MonthRow[]>([]);
const busy = ref(false);
const error = ref("");
let generation = 0;
async function load(reset = false) {
    if (reset) {
        page.value = 1;
        pages.value = 0;
        total.value = 0;
        rows.value = [];
    }
    const token = ++generation;
    busy.value = true;
    error.value = "";
    try {
        const data = await listMonths({
            view: view.value, month_key: month.value,
            employee_name: view.value === 'members' ? person.value : '',
            role_code: position.value, page: page.value, page_size: 10,
        });
        if (token === generation) {
            rows.value = page.value === 1 ? data.items : [...rows.value, ...data.items];
            pages.value = data.total_pages;
            total.value = data.total;
        }
    }
    catch (e) {
        if (token === generation) {
            error.value = getErrorMessage(e);
            if (page.value === 1)
                rows.value = [];
            else
                page.value--;
        }
    }
    finally {
        if (token === generation)
            busy.value = false;
    }
}
function open(row: MonthRow) { void router.push({ name: "mobile-weekly-report-month-detail", params: { employeeId: row.employee_id, monthKey: row.month_key } }); }
function resetFilters() {
    month.value = "";
    person.value = "";
    position.value = "";
    view.value = "members";
    void load(true);
}
onMounted(() => load());
function more(value: number) { page.value = value; void load(); }
</script>
<template>
<section class="month-list">
 <NoticeBridge :warning-message="error" />
 <MonthReportFilters v-model:month="month" v-model:position="position" v-model:view="view"
   v-model:person="person" :show-members="auth.effectiveRole?.scope !== 'self'"
   :disabled="busy" @search="load(true)" @reset="resetFilters" />
 <p v-if="busy && page===1">正在加载…</p>
 <MonthReportTable v-if="!busy || page > 1" :rows="rows" @open="open" />
 <ScrollLoadMore :page="page" :page-size="10" :total="total" :total-pages="pages" :disabled="busy" :error="error" @change="more" />
</section>
</template>
<style scoped src="./MonthReportList.css"></style>
