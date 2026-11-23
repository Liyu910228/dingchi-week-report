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
    color: ["#2d83ee", "#12b98d"],
    grid: { left: 34, right: 12, top: 24, bottom: 26 },
    tooltip: { trigger: "axis" },
    legend: { show: false },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: props.points.map((item) => item.label),
      axisLine: { lineStyle: { color: "#d8e8fa" } },
      axisTick: { show: false },
      axisLabel: { color: "#8096b5", fontSize: 11 },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 100,
      interval: 20,
      axisLabel: { color: "#8096b5", formatter: "{value}%", fontSize: 10 },
      splitLine: { lineStyle: { color: "#e8f1fb", type: "dashed" } },
    },
    series: [
      {
        name: "进展",
        type: "line",
        smooth: true,
        symbol: "circle",
        symbolSize: 6,
        data: props.points.map((item) => ({ value: item.progress, itemStyle: { color: progressColor(item.progress) } })),
        lineStyle: { width: 2.5 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "rgba(45,131,238,.22)" }, { offset: 1, color: "rgba(45,131,238,0)" }]) },
      },
      {
        name: "完成率",
        type: "line",
        smooth: true,
        symbol: "circle",
        symbolSize: 6,
        data: props.points.map((item) => ({ value: item.completion, itemStyle: { color: progressColor(item.completion) } })),
        lineStyle: { width: 2.5 },
      },
    ],
  })
}

function resizeChart() {
  chart?.resize()
}

onMounted(async () => {
  await nextTick()
  renderChart()
  window.addEventListener("resize", resizeChart)
})

watch(() => props.points, renderChart, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeChart)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div ref="chartElement" class="personal-trend-chart" aria-label="本周进展趋势图" />
</template>

<style scoped src="./PersonalTrendChart.css"></style>
