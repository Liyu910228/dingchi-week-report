import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import test from "node:test"
import ts from "typescript"
const source = readFileSync(new URL("../src/utils/date.ts", import.meta.url), "utf8")
const { outputText } = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022 } })
const { formatDateTime, formatPeriod } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`)
test("UTC 时间转换为北京时间，包含跨日和跨年", () => {
  assert.equal(formatDateTime("2026-10-14T05:16:46.546711+00:00"), "2026-10-14 13:16:46")
  assert.equal(formatDateTime("2026-12-31T20:30:00Z"), "2027-01-01 04:30:00")
})
test("带北京时间偏移的时间不重复加八小时", () => {
  assert.equal(formatDateTime("2026-10-14T13:16:46+08:00"), "2026-10-14 13:16:46")
})
test("Date 对象和其他时区表示同一时刻时保持一致", () => {
  assert.equal(formatDateTime(new Date("2026-10-14T05:16:46Z")), "2026-10-14 13:16:46")
  assert.equal(formatDateTime("2026-10-14T01:16:46-04:00"), "2026-10-14 13:16:46")
})
test("日期和无时区历史文本不改变日期或时刻", () => {
  assert.equal(formatDateTime("2026-10-14"), "2026-10-14 00:00:00")
  assert.equal(formatDateTime("2026-10-14 05:16:46"), "2026-10-14 05:16:46")
  assert.equal(formatPeriod("2026-10-12", "2026-10-18"), "2026-10-12 至 2026-10-18")
})
test("北京时间午夜不显示24点，空值及非法输入安全回退", () => {
  assert.equal(formatDateTime("2026-10-13T16:00:00Z"), "2026-10-14 00:00:00")
  assert.equal(formatDateTime(null), "—")
  assert.equal(formatDateTime(new Date("invalid")), "—")
  assert.equal(formatDateTime("invalid"), "invalid")
})
