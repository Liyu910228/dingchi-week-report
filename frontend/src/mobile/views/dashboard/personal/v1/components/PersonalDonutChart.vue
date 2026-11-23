<script setup lang="ts">
import * as echarts from "echarts"
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"

import type { DashboardDistribution } from "@/mobile/features/dashboard/types"

const props = defineProps<{ data: DashboardDistribution[] }>()
const chartElement = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

const total = () => props.data.reduce((sum, item) => sum + item.value, 0)

function renderChart() {
  if (!chartElement.value || total() === 0) {
    chart?.dispose()
    chart = null
    return
  }
  if (chart && chart.getDom() !== chartElement.value) {
    chart.dispose()
    chart = null
  }
  chart ||= echarts.init(chartElement.value)
  chart.setOption({
    animationDuration: 520,
    tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
    series: [{
      type: "pie",
      radius: ["52%", "84%"],
      center: ["50%", "50%"],
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

watch(
  () => props.data,
  async () => {
    // 数据由接口异步返回时，先等待 v-if 对图表容器完成挂载。
    await nextTick()
    renderChart()
  },
  { deep: true },
)

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeChart)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div v-if="total() === 0" class="personal-donut-empty">暂无数据</div>
  <div v-else ref="chartElement" class="personal-donut-chart" aria-label="分布图" />
</template>

<style scoped src="./PersonalDonutChart.css"></style>
