<script setup lang="ts">
import * as echarts from "echarts"
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"

import type { DashboardDistribution } from "@/mobile/features/dashboard/types"

const props = defineProps<{ data: DashboardDistribution[]; total: number }>()
const chartElement = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function renderChart() {
  if (!chartElement.value || !props.data.length) {
    chart?.dispose(); chart = null; return
  }
  chart ||= echarts.init(chartElement.value)
  chart.setOption({
    animationDuration: 520,
    tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
    series: [{ type: "pie", radius: ["54%", "76%"], center: ["50%", "50%"], itemStyle: { borderColor: "#fff", borderWidth: 3 }, label: { show: false }, data: props.data.map((item) => ({ name: item.name, value: item.value, itemStyle: { color: item.color } })) }],
  })
}

function resizeChart() { chart?.resize() }
onMounted(async () => { await nextTick(); renderChart(); window.addEventListener("resize", resizeChart) })
watch(() => props.data, async () => { await nextTick(); renderChart() }, { deep: true })
onBeforeUnmount(() => { window.removeEventListener("resize", resizeChart); chart?.dispose(); chart = null })
</script>

<template>
  <div class="leader-output-chart-wrap">
    <div v-if="!data.length" class="leader-chart-empty">暂无成果</div>
    <div v-else ref="chartElement" class="leader-output-chart" aria-label="成果构成图" />
    <div v-if="data.length" class="leader-output-center"><strong>{{ total }}</strong><span>总记录</span></div>
  </div>
</template>

<style scoped src="./LeaderOutputChart.css"></style>
