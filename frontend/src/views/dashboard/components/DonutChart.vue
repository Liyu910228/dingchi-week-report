<script setup lang="ts">
import * as echarts from "echarts"
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"

import type { DashboardDistribution } from "@/features/dashboard/types"

const props = defineProps<{ data: DashboardDistribution[] }>()
const chartElement = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function renderChart() {
  if (!chartElement.value) return
  chart ||= echarts.init(chartElement.value)
  chart.setOption({
    animationDuration: 600,
    tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
    series: [{
      type: "pie",
      radius: ["54%", "76%"],
      center: ["50%", "50%"],
      avoidLabelOverlap: true,
      itemStyle: { borderColor: "#fff", borderWidth: 3 },
      label: { show: false },
      data: props.data.map((item) => ({ name: item.name, value: item.value, itemStyle: { color: item.color } })),
    }],
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
watch(() => props.data, renderChart, { deep: true })
onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeChart)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div ref="chartElement" class="donut-chart" aria-label="任务状态分布图" />
</template>

<style scoped src="./DonutChart.css"></style>
