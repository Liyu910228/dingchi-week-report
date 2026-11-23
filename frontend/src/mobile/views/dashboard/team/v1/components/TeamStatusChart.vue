<script setup lang="ts">
import * as echarts from "echarts"
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue"

import type { DashboardDistribution } from "@/mobile/features/dashboard/types"

const props = defineProps<{ data: DashboardDistribution[]; total: number }>()
const chartElement = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function renderChart() {
  if (!chartElement.value || props.data.length === 0) {
    chart?.dispose()
    chart = null
    return
  }
  chart ||= echarts.init(chartElement.value)
  chart.setOption({
    animationDuration: 520,
    tooltip: { trigger: "item", formatter: "{b}: {c} ({d}%)" },
    series: [{
      type: "pie",
      radius: ["57%", "79%"],
      center: ["50%", "50%"],
      itemStyle: { borderColor: "#fff", borderWidth: 3 },
      label: { show: false },
      data: props.data.map((item) => ({ name: item.name, value: item.value, itemStyle: { color: item.color } })),
    }],
  })
}

function resizeChart() { chart?.resize() }

onMounted(async () => {
  await nextTick()
  renderChart()
  window.addEventListener("resize", resizeChart)
})

watch(() => props.data, async () => { await nextTick(); renderChart() }, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener("resize", resizeChart)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div class="team-status-chart-wrap">
    <div v-if="data.length === 0" class="team-status-empty">暂无任务</div>
    <div v-else ref="chartElement" class="team-status-chart" aria-label="任务状态分布图" />
    <div v-if="data.length" class="team-status-center">
      <strong>{{ total }}</strong>
      <span>总任务</span>
    </div>
  </div>
</template>

<style scoped src="./TeamStatusChart.css"></style>
