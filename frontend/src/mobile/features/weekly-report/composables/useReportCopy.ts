import { ref } from "vue"
import { copyReport } from "../api"
import type { WeeklyReport } from "../types"

export function useReportCopy(reload: () => Promise<void>) {
  const busy = ref(false)
  const message = ref("")
  const title = ref("")
  async function copy(report: WeeklyReport) {
    if (busy.value) return
    busy.value = true
    try {
      const result = await copyReport(report.id)
      title.value = "复制成功"
      message.value = `已生成 ${result.period_start} 至 ${result.period_end} 的周报，可在列表中继续编辑。`
      await reload()
    } catch (error) {
      title.value = "无法复制周报"
      message.value = error instanceof Error ? error.message : "复制失败，请稍后重试。"
    } finally {
      busy.value = false
    }
  }
  return { busy, message, title, copy }
}
