<script setup lang="ts">
import { progressColor } from "@/mobile/utils/progress-color"
import * as echarts from "echarts"
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"

import type { DashboardTrendPoint } from "@/mobile/features/dashboard/types"

const props = defineProps<{ points: DashboardTrendPoint[] }>()
const chartElement = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function renderChart() {
  if (!chartElement.value) return
  chart ||= echarts.init(chartElement.value)
  chart.setOption({
    animationDuration: 550,
    color: ["#0878ff", "#00c3a5"],
    grid: { left: 37, right: 12, top: 26, bottom: 24 },
    tooltip: { trigger: "axis" },
    legend: { show: false },
    xAxis: { type: "category", boundaryGap: false, data: props.points.map((item) => item.label), axisLine: { lineStyle: { color: "#d8e8fa" } }, axisTick: { show: false }, axisLabel: { color: "#8096b5", fontSize: 10 } },
    yAxis: { type: "value", min: 0, max: 100, interval: 20, axisLabel: { color: "#8096b5", formatter: "{value}%", fontSize: 10 }, splitLine: { lineStyle: { color: "#e8f1fb", type: "dashed" } } },
    series: [
      { name: "任务进度", type: "line", smooth: true, symbol: "circle", symbolSize: 6, data: props.points.map((item) => ({ value: item.progress, itemStyle: { color: progressColor(item.progress) } })), lineStyle: { width: 2.5 }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "rgba(45,131,238,.2)" }, { offset: 1, color: "rgba(45,131,238,0)" }]) } },
      { name: "完成率", type: "line", smooth: true, symbol: "circle", symbolSize: 6, data: props.points.map((item) => ({ value: item.completion, itemStyle: { color: progressColor(item.completion) } })), lineStyle: { width: 2.5 } },
    ],
  })
}

function resizeChart() { chart?.resize() }
onMounted(async () => { await nextTick(); renderChart(); window.addEventListener("resize", resizeChart) })
watch(() => props.points, renderChart, { deep: true })
onBeforeUnmount(() => { window.removeEventListener("resize", resizeChart); chart?.dispose(); chart = null })
</script>

<template>
  <div v-if="!points.length" class="leader-chart-empty">暂无趋势数据</div>
  <div v-else ref="chartElement" class="leader-trend-chart" aria-label="总体执行趋势图" />
</template>

<style scoped src="./LeaderTrendChart.css"></style>
