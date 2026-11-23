<script setup lang="ts">
import { progressColor } from "@/mobile/utils/progress-color"
import * as echarts from "echarts"
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"

const props = defineProps<{ value: number }>()
const chartElement = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function renderChart() {
  if (!chartElement.value) return
  chart ||= echarts.init(chartElement.value)
  chart.setOption({
    animationDuration: 600,
    series: [{ type: "gauge", startAngle: 90, endAngle: -270, radius: "86%", pointer: { show: false }, progress: { show: true, roundCap: true, width: 16, itemStyle: { color: progressColor(props.value) } }, axisLine: { lineStyle: { width: 16, color: [[1, "#e1efff"]] } }, axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false }, anchor: { show: false }, detail: { valueAnimation: true, offsetCenter: [0, "4%"], fontSize: 32, fontWeight: 750, color: progressColor(props.value), formatter: "{value}%" }, data: [{ value: Math.round(Math.min(100, Math.max(0, props.value))) }] }],
  })
}

function resizeChart() { chart?.resize() }
onMounted(async () => { await nextTick(); renderChart(); window.addEventListener("resize", resizeChart) })
watch(() => props.value, renderChart)
onBeforeUnmount(() => { window.removeEventListener("resize", resizeChart); chart?.dispose(); chart = null })
</script>

<template><div ref="chartElement" class="leader-gauge-chart" aria-label="总体完成率" /></template>

<style scoped src="./LeaderGaugeChart.css"></style>
