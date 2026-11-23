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
    animationDuration: 650,
    color: ["#2f80ed", "#11b883"],
    grid: { left: 42, right: 18, top: 22, bottom: 28 },
    tooltip: { trigger: "axis" },
    legend: {
      top: 0,
      right: 0,
      icon: "circle",
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { color: "#6e82a6", fontSize: 12 },
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: props.points.map((item) => item.label),
      axisLine: { lineStyle: { color: "#d9e8fa" } },
      axisTick: { show: false },
      axisLabel: { color: "#8094b4", fontSize: 11 },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 100,
      interval: 20,
      axisLabel: { color: "#8094b4", formatter: "{value}%", fontSize: 11 },
      splitLine: { lineStyle: { color: "#e8f1fb", type: "dashed" } },
    },
    series: [
      {
        name: "进展",
        type: "line",
        smooth: true,
        symbol: "circle",
        symbolSize: 7,
        data: props.points.map((item) => ({ value: item.progress, itemStyle: { color: progressColor(item.progress) } })),
        lineStyle: { width: 3 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: "rgba(47,128,237,.25)" }, { offset: 1, color: "rgba(47,128,237,0)" }]) },
      },
      {
        name: "完成率",
        type: "line",
        smooth: true,
        symbol: "circle",
        symbolSize: 7,
        data: props.points.map((item) => ({ value: item.completion, itemStyle: { color: progressColor(item.completion) } })),
        lineStyle: { width: 3 },
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
  <div ref="chartElement" class="trend-chart" aria-label="本周进展趋势图" />
</template>

<style scoped src="./TrendChart.css"></style>
