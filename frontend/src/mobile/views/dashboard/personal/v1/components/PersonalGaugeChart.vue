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
    animationDuration: 650,
    series: [{
      type: "gauge",
      startAngle: 90,
      endAngle: -269.9999,
      min: 0,
      max: 100,
      radius: "92%",
      pointer: { show: false },
      progress: { show: true, roundCap: true, width: 17, itemStyle: { color: progressColor(props.value) } },
      axisLine: { lineStyle: { width: 17, color: [[1, "#dcecff"]] } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      detail: { valueAnimation: true, offsetCenter: [0, "0%"], fontSize: 28, fontWeight: 700, color: progressColor(props.value), formatter: "{value}%" },
      data: [{ value: Math.round(props.value) }],
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

watch(() => props.value, renderChart)

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeChart)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div ref="chartElement" class="personal-gauge-chart" aria-label="整体完成率" />
</template>

<style scoped src="./PersonalGaugeChart.css"></style>
