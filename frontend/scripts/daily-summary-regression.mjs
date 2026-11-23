import { build } from "esbuild"
import { resolve } from "node:path"

const result = await build({
  stdin: {
    contents: `
      import { reactive } from 'vue'
      import { useCommonDailySummary as pc } from './src/features/submissions/useCommonDailySummary'
      import { useCommonDailySummary as mobile } from './src/mobile/features/submissions/useCommonDailySummary'

      for (const useSummary of [pc, mobile]) {
        const input = reactive({
          period_start: '2026-11-02',
          parts: [{
            role_code: 'a',
            payload: { daily_tasks: [{ id: '1', work_date: '2026-11-03', work_content: '总结' }] },
            detail: { report: { id: 'ra', period_end: '2026-11-08' }, daily_tasks: [] },
          }],
        })
        const common = useSummary(input)
        input.period_start = '2026-11-09'
        if (common.report.value.period_end !== '2026-11-15') throw Error('日报日期范围未同步')
        if (common.tasks.value[0].work_date !== '2026-11-10') throw Error('已有日报日期未随周期移动')
        input.period_start = '2026-11-02'
        if (common.tasks.value[0].work_date !== '2026-11-03') throw Error('切回原周期时日报日期未复原')
      }
      console.log('PASS: PC 和 mobile 的日报日期随周报周期同步')
    `,
    resolveDir: process.cwd(),
    loader: "ts",
  },
  bundle: true,
  write: false,
  format: "esm",
  platform: "node",
  alias: { "@": resolve("src") },
})

try {
  await import(`data:text/javascript;base64,${Buffer.from(result.outputFiles[0].text).toString("base64")}`)
} catch (error) {
  console.error(error.message)
  process.exitCode = 1
}
